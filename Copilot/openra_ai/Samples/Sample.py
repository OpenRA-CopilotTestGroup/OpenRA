# COPILOT_PROMPT_IGNORE
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam
from OpenRA_Copilot_Library import Location

api = OpenRA.GameAPI("localhost")
# api.produce_units('井', 1200)
# api.produce_units('电塔', 20)
infantry = api.query_actor(TargetsQueryParam(type=['步兵'], faction='己方'))
# light_tanks = api.query_actor(TargetsQueryParam(type=['防空车'], faction='己方'))
apc = api.query_actor(TargetsQueryParam(type=['装甲车'], faction='己方'))
enemy_base = api.query_actor(TargetsQueryParam(type=['基地'], faction='敌方'))[0]
base_position = enemy_base.position
base_position = Location(base_position.x + 3, base_position.y + 4)
mcv = api.query_actor(TargetsQueryParam(type=['基地车'], faction='己方'))

allthing = api.query_actor(TargetsQueryParam(faction='己方'))
print(infantry)
api.repair_units(allthing)
# api.move_units_by_location(infantry, apc[0].position if apc else base_position)
api.move_units_by_location(infantry, base_position)
