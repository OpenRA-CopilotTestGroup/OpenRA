# COPILOT_PROMPT_IGNORE
# 这个是临时测试代码
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam
from OpenRA_Copilot_Library import Location
import time

api = OpenRA.GameAPI("localhost")

infantry = api.query_actor(TargetsQueryParam(type=['步兵'], faction='己方'))
tanks = api.query_actor(TargetsQueryParam(type=['防空车'], faction='己方'))
armored_car = api.query_actor(TargetsQueryParam(type=['装甲车'], faction='己方'))[0]
enemy_base = api.query_actor(TargetsQueryParam(type=['基地'], faction='敌方'))[0]
base_position = enemy_base.position
home_base = api.query_actor(TargetsQueryParam(type=['基地'], faction='己方'))[0]
home_base_position = home_base.position

for soldier in infantry:
    path = api.find_path([soldier], base_position, '左侧路径')
    api.move_units_by_path([soldier], path)

for soldier in tanks:
    path = api.find_path([soldier], base_position, '右侧路径')
    api.move_units_by_path([soldier], path)



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

