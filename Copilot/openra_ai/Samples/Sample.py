# COPILOT_PROMPT_IGNORE
# 这个是临时测试代码
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam
from OpenRA_Copilot_Library import Location
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

for ftrk in team_1:
    print("队伍1防空车位置：", ftrk.position, "队伍1防空车ID：", ftrk.actor_id)
for ftrk in team_2:
    print("队伍2防空车位置：", ftrk.position, "队伍2防空车ID：", ftrk.actor_id)

path1 = api.find_path(team_1, base_position, '左侧路径')
path2 = api.find_path(team_2, base_position, '右侧路径')

print("队伍1开始沿路径移动")
api.move_units_by_path(team_1, path1)

print("队伍2开始沿路径移动")
api.move_units_by_path(team_2, path2)

# infantry = api.query_actor(TargetsQueryParam(type=['步兵'], faction='己方'))
# tanks = api.query_actor(TargetsQueryParam(type=['防空车'], faction='己方'))
# armored_car = api.query_actor(TargetsQueryParam(type=['装甲车'], faction='己方'))[0]
# enemy_base = api.query_actor(TargetsQueryParam(type=['基地'], faction='敌方'))[0]
# base_position = enemy_base.position
# home_base = api.query_actor(TargetsQueryParam(type=['基地'], faction='己方'))[0]
# home_base_position = home_base.position

# for soldier in infantry:
#     path = api.find_path([soldier], base_position, '左侧路径')
#     api.move_units_by_path([soldier], path)

# for soldier in tanks:
#     path = api.find_path([soldier], base_position, '右侧路径')
#     api.move_units_by_path([soldier], path)


# api = OpenRA.GameAPI("localhost")
# api.produce_units('井', 10)
# # api.produce_units('井', 1200)
# # api.produce_units('电塔', 20)
# infantry = api.query_actor(TargetsQueryParam(type=['步兵'], faction='己方'))
# # light_tanks = api.query_actor(TargetsQueryParam(type=['防空车'], faction='己方'))
# apc = api.query_actor(TargetsQueryParam(type=['装甲车'], faction='己方'))
# home = api.query_actor(TargetsQueryParam(type=['基地'], faction='己方'))[0]
# enemy_base = api.query_actor(TargetsQueryParam(type=['基地'], faction='敌方'))[0]
# base_position = enemy_base.position
# base_position = Location(base_position.x + 3, base_position.y + 4)
# mcv = api.query_actor(TargetsQueryParam(type=['基地车'], faction='己方'))

# allthing = api.query_actor(TargetsQueryParam(faction='己方'))
# # print(infantry)
# # api.repair_units(allthing)
# # api.move_units_by_location(infantry, apc[0].position if apc else base_position)
# api.move_units_by_location(infantry, base_position)

# while infantry:
#     for s in infantry:
#         if not api.update_actor(s):
#             infantry.remove(s)
#         if api.unit_range_query([s]):
#             api.move_units_by_location([s], home.position)
#             infantry.remove(s)
#     time.sleep(0.1)
