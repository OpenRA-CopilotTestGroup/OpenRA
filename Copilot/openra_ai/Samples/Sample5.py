# 该代码对应指令为：所有步兵进攻地方基地，每一个遇见敌人的兵，立马返回
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam
from OpenRA_Copilot_Library import Location
import time

api = OpenRA.GameAPI("localhost")
infantry = api.query_actor(TargetsQueryParam(type=['步兵'], faction='己方'))

home = api.query_actor(TargetsQueryParam(type=['基地'], faction='己方'))[0]
enemy_base = api.query_actor(TargetsQueryParam(type=['基地'], faction='敌方'))[0]
base_position = enemy_base.position
api.move_units_by_location(infantry, base_position)

while infantry:
    for s in infantry:
        #用于判断s这个士兵是否还存活，能否更新信息
        if not api.update_actor(s):
            infantry.remove(s)
        if api.unit_range_query([s]):
            api.move_units_by_location([s], home.position)
            infantry.remove(s)
    time.sleep(0.2)

