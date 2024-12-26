# 该代码对应指令为：坦克突击，攻击敌方炮兵
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam, Location
import time

api = OpenRA.GameAPI("localhost")

# 查询己方坦克单位
tanks = api.query_actor(TargetsQueryParam(type=["坦克"], faction="自己"))
if not tanks:
    raise RuntimeError("没有坦克，无法执行任务")

# 查询敌方炮兵单位
artilleries = api.query_actor(TargetsQueryParam(type=["炮兵"], faction="敌方"))
if not artilleries:
    raise RuntimeError("未找到敌方炮兵，无法执行任务")

# 选取最近的炮兵作为目标
def find_closest_target(unit, targets):
    min_distance = float("inf")
    closest_target = None
    for target in targets:
        distance = unit.position.manhattan_distance(target.position)
        if distance < min_distance:
            min_distance = distance
            closest_target = target
    return closest_target

# 攻击函数，失败重试
def attack_with_retry(unit, target, fallback_position, max_retries=5):
    retries = 0
    while retries < max_retries:
        success = api.attack_target(unit, target)
        if success:
            print(f"单位 {unit.actor_id} 成功攻击目标 {target.actor_id}")
            return True
        print(f"单位 {unit.actor_id} 攻击失败，尝试移动后重试")
        api.move_units_by_location([unit], fallback_position)  # 移动到回退位置
        time.sleep(1)  # 等待移动完成
        if not api.update_actor(unit):  # 检查单位是否存活
            print(f"单位 {unit.actor_id} 已被摧毁，无法继续攻击")
            return False
        retries += 1
    print(f"单位 {unit.actor_id} 攻击目标失败，已达到最大重试次数")
    return False

# 开始攻击
active_units = set(tanks)
while active_units and artilleries:
    for unit in list(active_units):
        if not api.update_actor(unit):  # 检查坦克是否存活
            print(f"单位 {unit.actor_id} 已被摧毁，移除队伍")
            active_units.remove(unit)
            continue

        # 查找最近的炮兵目标
        target = find_closest_target(unit, artilleries)
        if not target:
            print("没有目标可以攻击")
            break

        # 如果目标存活，尝试攻击
        fallback_position = Location(unit.position.x - 3, unit.position.y)  # 简单回退
        if api.update_actor(target):
            if attack_with_retry(unit, target, fallback_position):
                if not api.update_actor(target):  # 检查目标是否被摧毁
                    print(f"敌方炮兵 {target.actor_id} 被摧毁")
                    artilleries.remove(target)
        else:
            print(f"敌方炮兵 {target.actor_id} 已被摧毁")
            artilleries.remove(target)

    time.sleep(0.5)  # 统一的循环节奏控制

print("任务完成")
