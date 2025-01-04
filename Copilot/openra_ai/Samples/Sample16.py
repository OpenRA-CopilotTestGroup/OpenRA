# 该代码对应指令为：实时汇报屏幕中所有单位
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam
import time

api = OpenRA.GameAPI("localhost")

screen_units = set()

print("开始监控屏幕内单位的进入和离开事件")
while True:
    
    # screen_info = api.screen_info_query()
    # screen_min = screen_info.ScreenMin
    # screen_max = screen_info.ScreenMax

    # 查询屏幕范围内的所有单位
    visible_units = api.query_actor(
        TargetsQueryParam(
            type=[],  # 查询所有类型的单位
            range="screen",  # 查询屏幕范围内的单位
            restrain=[{"visible": True}]  # 必须可见
        )
    )

    # 筛选出在屏幕范围内的单位
    # current_screen_units = {
    #     unit.actor_id
    #     for unit in visible_units
    #     if screen_min.x <= unit.position.x <= screen_max.x and
    #        screen_min.y <= unit.position.y <= screen_max.y
    # }
    current_screen_units = {unit.actor_id for unit in visible_units}

    new_units = current_screen_units - screen_units
    for unit_id in new_units:
        unit = next(unit for unit in visible_units if unit.actor_id == unit_id)
        print(
            f"单位进入屏幕：ID={unit.actor_id}, 类型={unit.type}, 位置=({unit.position.x}, {unit.position.y})")

    removed_units = screen_units - current_screen_units
    for unit_id in removed_units:
        print(f"单位离开屏幕：ID={unit_id}")

    screen_units = current_screen_units

    time.sleep(0.5)
