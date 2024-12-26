# 该代码对应指令为：防空车分成两队攻击敌方基地
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam
import time

api = OpenRA.GameAPI("localhost")

# 查询防空车单位
ftrks = api.query_actor(TargetsQueryParam(type=["防空车"], faction="自己"))
if not ftrks:
    raise RuntimeError("没有防空车，无法执行任务")

# 查询敌方基地位置
enemy_bases = api.query_actor(TargetsQueryParam(type=["基地"], faction="敌方"))
if not enemy_bases:
    raise RuntimeError("未找到敌方基地")
enemy_base = enemy_bases[0]
base_position = enemy_base.position

midpoint = len(ftrks) // 2
team_1 = ftrks[:midpoint]
team_2 = ftrks[midpoint:]

path1 = api.find_path(team_1, base_position, '左侧路径')
path2 = api.find_path(team_2, base_position, '右侧路径')

print("队伍1开始沿路径移动")
api.move_units_by_path(team_1, path1)

print("队伍2开始沿路径移动")
api.move_units_by_path(team_2, path2)

active_units = set(team_1 + team_2)
while active_units:
    if not api.update_actor(enemy_base):
        print(f"地方基地 {enemy_base.actor_id} 已被摧毁，完成目标！")
        break
    for unit in list(active_units):
        if not api.update_actor(unit):  # 检查存活状态
            print(f"单位 {unit.actor_id} 已被摧毁，移除队伍")
            active_units.remove(unit)
            continue
        current_position = unit.position
        if current_position.manhattan_distance(base_position) <= 3:
            if api.attack_target(unit, enemy_base):
                active_units.remove(unit)  # 攻击成功后移除队伍
            else:
                api.move_units_by_location([unit],base_position)
    time.sleep(0.5)

print("任务完成")
