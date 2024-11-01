# 该代码对应指令为：先让吉普去敌方基地勾引一下，然后士兵和坦克一起迎上去打敌方基地

import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam
import time

api = OpenRA.GameAPI("localhost")
jeeps = api.query_actor(OpenRA.TargetsQueryParam(type=["吉普"], faction="自己"))
rocket_soldiers = api.query_actor(OpenRA.TargetsQueryParam(type=["火箭筒"], faction="自己"))
tanks = api.query_actor(OpenRA.TargetsQueryParam(type=["v2"], faction="自己"))
jeep = jeeps[0]
initial_position = jeep.position
while True:
    api.update_actor(jeep)
    enemy_base = api.query_actor(OpenRA.TargetsQueryParam(type=["基地"], faction="敌方"))[0]
    base_position = enemy_base.position
# 吉普向敌方基地移动
    api.move_units_by_location([jeep], base_position)
    # 检测有没有碰到人
    enemies_near_motorcycle = api.query_actor(OpenRA.TargetsQueryParam(faction="敌方", location=jeep.position, restrain=[{"distance": 5}]))
    if enemies_near_motorcycle:
        # 有人就往初始位置跑
        retreat_path = api.find_path([jeep], initial_position, '最短路径')
        if retreat_path:
            intermediate_position = retreat_path[len(retreat_path) // 2]
            api.move_units_by_location([jeep], initial_position)
            # 然后火箭和坦克靠上去
            api.move_units_by_location(rocket_soldiers, jeep.position, True)
            api.move_units_by_location(tanks, jeep.position, True)
            break
    time.sleep(2)


