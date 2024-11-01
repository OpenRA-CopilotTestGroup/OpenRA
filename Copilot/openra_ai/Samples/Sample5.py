# COPILOT_PROMPT_IGNORE
# 该代码对应指令为：修理基地
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam

api = OpenRA.GameAPI("localhost")

mammoth_tanks = api.query_actor(TargetsQueryParam(type=["猛犸"], group_id=[1]))
api.stop(mammoth_tanks)
