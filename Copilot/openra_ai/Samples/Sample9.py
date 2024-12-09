# 该代码对应指令为：电不够的时候帮我补一下电
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam
import time
api = OpenRA.GameAPI("localhost")

while True:
    playerinfo = api.player_base_info_query()
    if playerinfo.Power < 20:
        if api.able_to_produce("核电厂"):
            p1 = api.produce_units("核电厂", 1)
        else:
            p1 = api.produce_units("电厂", 1)
        api.wait(p1)
    time.sleep(0.5)
