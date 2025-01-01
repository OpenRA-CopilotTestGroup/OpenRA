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
    # 先取第一个敌人
    enemy = enemies_in_proximity[0]
    if api.update_actor(enemy):
        enemy_pos = enemy.position

        # 坦克直接开到敌人脸上
        tank_path = api.find_path(tanks, enemy_pos, "最短路径")
        if tank_path:
            api.move_units_by_path(tanks, tank_path)

        # 步兵保持攻击距离（5格），因此需要判断当前位置与敌人距离
        for soldier in infantry:
            if not api.update_actor(soldier):
                continue
            dx = soldier.position.x - enemy_pos.x
            dy = soldier.position.y - enemy_pos.y
            current_dist = abs(dx) + abs(dy)
            desired_dist = 5

            # 如果距敌人小于5格，就后撤，否则前进（保持在5格范围）
            move_offset = desired_dist - current_dist

            new_x = soldier.position.x - (dx / current_dist) * move_offset if current_dist else soldier.position.x
            new_y = soldier.position.y - (dy / current_dist) * move_offset if current_dist else soldier.position.y

            # 路径点需要整数坐标
            new_x = int(round(new_x))
            new_y = int(round(new_y))
            retreat_path = api.find_path([soldier], Location(new_x, new_y), "最短路径")
            if retreat_path:
                api.move_units_by_path([soldier], retreat_path)
else:
    # 如果周围没有敌人，就尝试查询敌方基地
    enemy_base = api.query_actor(TargetsQueryParam(type=["基地"], faction="敌方"))
    if enemy_base:
        # 让坦克稍微前进一点
        base_pos = enemy_base[0].position
        path_to_base = api.find_path(tanks, base_pos, "最短路径")
        if path_to_base:
            partial_path = path_to_base[: max(1, len(path_to_base) // 3)]
            api.move_units_by_path(tanks, partial_path)
    else:
        print("附近没有敌人，也未发现敌方基地。无需采取行动。")
