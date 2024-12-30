# 该代码对应指令为：坦克突击，攻击敌方士兵
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam
import time

api = OpenRA.GameAPI("localhost")

tanks = api.query_actor(TargetsQueryParam(type=["坦克"], faction="自己"))
if not tanks:
    raise RuntimeError("没有坦克，无法执行任务")

soldiers = api.query_actor(TargetsQueryParam(type=["士兵"], faction="敌方", restrain=[{"visible": True}]))
if not soldiers:
    raise RuntimeError("未找到敌方士兵，无法执行任务")

# 查找最近的目标
def find_closest_target(unit, targets):
    min_distance = float("inf")
    closest_target = None
    for target in targets:
        distance = unit.position.manhattan_distance(target.position)
        if distance < min_distance:
            min_distance = distance
            closest_target = target
    return closest_target

active_units = set(tanks)
while active_units and soldiers:
    #直接重新拿所有士兵
    soldiers = api.query_actor(TargetsQueryParam(type=["士兵"], faction="敌方", restrain=[{"visible": True}]))

    if not soldiers:
        print("所有士兵已被摧毁，完成任务")
        active_units.clear()
        break
    for unit in list(active_units):
        if not api.update_actor(unit):  
            print(f"单位 {unit.actor_id} 已被摧毁，移除队伍")
            active_units.remove(unit)
            continue

        # 查找最近的士兵目标
        target = find_closest_target(unit, soldiers)

        print(f"单位 {unit.actor_id} 攻击目标 {target.actor_id}，位置=({target.position.x}, {target.position.y})")
        # 坦克可以碾压敌方士兵，因此不用attackmove，attackmove会导致坦克停下来，直接move到士兵位置攻击
        api.move_units_by_location([unit], target.position)
      
    time.sleep(1)  

print("任务完成")