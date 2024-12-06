# COPILOT_PROMPT_IGNORE
# 该代码对应指令为：装甲车去对面基地勾引一下，遇到敌人就回来点，然后把步兵和防空车压上去，等都到了就两路夹击地方基地
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam

api = OpenRA.GameAPI("localhost")

tanks = api.query_actor(TargetsQueryParam(type=['防空车'], faction='己方'))
armored_car = api.query_actor(TargetsQueryParam(type=['装甲车'], faction='己方'))[0]
enemy_base = api.query_actor(TargetsQueryParam(type=['基地'], faction='敌方'))[0]
api.attack_target(tanks,enemy_base)
