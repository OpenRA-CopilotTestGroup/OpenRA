# 该代码对应指令为：一半步兵编成1组进攻地方基地，每一个遇见敌人的兵，立马返回
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import *
import time

api = OpenRA.GameAPI("localhost")
infantry = api.query_actor(TargetsQueryParam(type=['步兵'], faction='己方'))
num = len(infantry)
infantry_half = infantry[:num//2]
api.form_group(infantry_half, 1)

home = api.query_actor(TargetsQueryParam(type=['基地'], faction='己方'))[0]
enemy_base = api.query_actor(TargetsQueryParam(type=['基地'], faction='敌方'))[0]
base_position = enemy_base.position
api.move_units_by_location(infantry_half, base_position)

while infantry_half:
    for s in infantry_half:
        # 用于判断s这个士兵是否还存活，能否更新信息
        if not api.update_actor(s):
            infantry_half.remove(s)
        if api.unit_range_query([s]):
            api.move_units_by_location([s], home.position)
            infantry_half.remove(s)
    time.sleep(0.2)
