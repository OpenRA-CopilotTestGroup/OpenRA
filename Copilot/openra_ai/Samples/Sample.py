# COPILOT_PROMPT_IGNORE
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam

GAME_API = OpenRA.GameAPI("localhost")


infantry = GAME_API.query_actor(TargetsQueryParam(type=['步兵'], faction='己方'))
light_tanks = GAME_API.query_actor(TargetsQueryParam(type=['防空车'], faction='己方'))
enemy_base = GAME_API.query_actor(TargetsQueryParam(type=['基地'], faction='敌方'))[0]
base_position = enemy_base.position

mcv = GAME_API.query_actor(TargetsQueryParam(type=['基地车'], faction='己方'))

GAME_API.move_camera_to(mcv)
