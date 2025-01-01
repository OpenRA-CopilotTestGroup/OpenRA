# 该代码对应指令为：坦克顶前面吸收伤害，步兵往后退一点
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam, Location

api = OpenRA.GameAPI("localhost")

tanks = api.query_actor(TargetsQueryParam(type=["坦克"], faction="己方"))
infantry = api.query_actor(TargetsQueryParam(type=["步兵"], faction="己方"))

if not tanks and not infantry:
    raise RuntimeError("没有找到坦克或步兵")


def find_nearby_enemies(units, distance=10):
    nearby_enemies = []
    for unit in units:
        if not api.update_actor(unit):
            continue
        query = TargetsQueryParam(
            faction="敌方",
            location=unit.position,
            restrain=[{"distance": distance}, {"visible": True}]
        )
        found = api.query_actor(query)
        if found:
            nearby_enemies.extend(found)
    return nearby_enemies


enemies_in_proximity = find_nearby_enemies(tanks + infantry, distance=15)

if enemies_in_proximity:
    # 获取所有敌人的位置
    enemy_positions = [enemy.position for enemy in enemies_in_proximity if api.update_actor(enemy)]

    # 坦克直接开到第一个敌人脸上
    primary_enemy = enemies_in_proximity[0]
    api.move_units_by_location(tanks, primary_enemy.position)

    # 步兵保持攻击距离（5格），并考虑多个敌人
    for soldier in infantry:
        if not api.update_actor(soldier):
            continue

        desired_dist = 5

        # 找到士兵当前位置0到2*desired_dist范围内的所有可能位置
        potential_positions = []
        for dx in range(-2 * desired_dist, 2 * desired_dist + 1):
            for dy in range(-2 * desired_dist, 2 * desired_dist + 1):
                potential_positions.append(Location(soldier.position.x + dx, soldier.position.y + dy))

        # 筛选满足以下条件的位置：
        # 1. 离最近的敌人距离为desired_dist
        # 2. 离其他所有敌人大于等于desired_dist
        safe_positions = []
        for pos in potential_positions:
            distances = [pos.manhattan_distance(enemy_pos) for enemy_pos in enemy_positions]
            if min(distances) == desired_dist and all(dist >= desired_dist for dist in distances):
                safe_positions.append(pos)

        # 找到离士兵当前位置最近的安全位置
        best_position = min(
            (pos for pos in safe_positions),
            key=lambda pos: soldier.position.manhattan_distance(pos),
            default=None  # 如果没有有效点，则跳过移动
        )

        if best_position:
            api.move_units_by_location([soldier], best_position)

else:
    # 如果周围没有敌人，就尝试查询敌方基地
    enemy_base = api.query_actor(TargetsQueryParam(type=["基地"], faction="敌方"))
    if enemy_base:
        # 让坦克稍微前进一点
        base_pos = enemy_base[0].position
        path_to_base = api.find_path(tanks, base_pos, "最短路径")
        if path_to_base:
            api.move_units_by_location(
                tanks,path_to_base[max(1, len(path_to_base) // 3):])
    else:
        print("附近没有敌人，也未发现敌方基地。无需采取行动。")
