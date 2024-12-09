# 该代码对应指令为：装甲车去对面基地勾引一下，遇到敌人就回来点，然后把步兵和防空车压上去，等都到了就两路夹击地方基地
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import *
import time

api = OpenRA.GameAPI("localhost")

infantry = api.query_actor(TargetsQueryParam(type=['步兵'], faction='己方'))
tanks = api.query_actor(TargetsQueryParam(type=['防空车'], faction='己方'))
armored_car = api.query_actor(TargetsQueryParam(type=['装甲车'], faction='己方'))[0]
enemy_base = api.query_actor(TargetsQueryParam(type=['基地'], faction='敌方'))[0]
base_position = enemy_base.position
home_base = api.query_actor(TargetsQueryParam(type=['基地'], faction='己方'))[0]
home_base_position = home_base.position

api.move_units_by_location([armored_car], base_position)

while not api.unit_range_query([armored_car]):
    time.sleep(0.5)

path = api.find_path(infantry, base_position, '最短路')
midpoint = path[len(path)//2]
api.move_units_by_location([armored_car], midpoint)

api.move_units_by_location(infantry, midpoint)
api.move_units_by_location(tanks, midpoint)

def all_units_arrived(units, position):
    for unit in units:
        if not api.update_actor(unit) or unit.position.manhattan_distance(position) > 5:
            return False
    return True

while not all_units_arrived(infantry + tanks, midpoint):
    time.sleep(0.5)

for soldier in infantry:
    path = api.find_path([soldier], base_position, '左侧路径')
    api.move_units_by_path([soldier], path)

for soldier in tanks:
    path = api.find_path([soldier], base_position, '右侧路径')
    api.move_units_by_path([soldier], path)
