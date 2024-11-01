# 该代码对应指令为：先建造一个电厂，再造一个兵营, 造5个步兵，两个火箭炮，补一个矿场。等造好步兵和火箭后，所有步兵和火箭攻击敌方基地。

import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam

api = OpenRA.GameAPI("localhost")
if api.able_to_produce("电厂"):
    p1 = api.produce_units("电厂", 1)
    api.wait(p1)
if api.able_to_produce("兵营"):
    p2 = api.produce_units("兵营", 1)
    api.wait(p2)
if api.able_to_produce("步兵"):
    p3 = api.produce_units("步兵", 5)
    p4 = api.produce_units("火箭筒兵", 2)
    api.wait(p3)
    api.wait(p4)
api.produce_units("矿场", 1)
infantry = api.query_actor(
    TargetsQueryParam(type=["步兵"], faction="自己"))
rocket_soldiers = api.query_actor(
    TargetsQueryParam(type=["火箭筒兵"], faction="自己"))
enemy_base = api.query_actor(
    TargetsQueryParam(type=["基地"], faction="敌方"))[0]
base_position = enemy_base.position
units_to_attack = infantry + rocket_soldiers
api.move_units_by_location(units_to_attack, base_position, attackmove=True)
