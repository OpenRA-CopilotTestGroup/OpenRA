import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam
from openai import OpenAI

GAME_API = OpenRA.GameAPI("localhost")

if GAME_API.able_to_produce('电厂'):
    p1 = GAME_API.produce_units('电厂', 1)
    GAME_API.wait(p1)

if GAME_API.able_to_produce('兵营'):
    p2 = GAME_API.produce_units('兵营', 1)
    GAME_API.wait(p2)

if GAME_API.able_to_produce('步兵'):
    p3 = GAME_API.produce_units('步兵', 5)
    if GAME_API.able_to_produce('轻坦克'):
        p4 = GAME_API.produce_units('轻坦克', 2)
        GAME_API.wait(p4)
    GAME_API.wait(p3)

if GAME_API.able_to_produce('矿场'):
    p5 = GAME_API.produce_units('矿场', 1)

infantry = GAME_API.query_actor(TargetsQueryParam(type=['步兵'], faction='己方'))
light_tanks = GAME_API.query_actor(TargetsQueryParam(type=['轻坦克'], faction='己方'))
enemy_base = GAME_API.query_actor(TargetsQueryParam(type=['基地'], faction='敌方'))[0]
base_position = enemy_base.position

units_to_attack = infantry + light_tanks
GAME_API.move_units_by_location(units_to_attack, base_position, attackmove=True)
