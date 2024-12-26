# 该代码对应指令为：随时汇报敌人所有可见战斗单位
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam, Location
import time

api = OpenRA.GameAPI("localhost")

# 初始化已报告单位的集合
current_units = set()  # 当前可见的单位集合

print("开始监控可见的敌方战斗单位")
while True:
    # 查询当前可见的敌方战斗单位
    visible_units = api.query_actor(
        TargetsQueryParam(type=["战斗单位"], faction="敌方", restrain=[{"visible": True}])
    )
    visible_unit_ids = {unit.actor_id for unit in visible_units}

    # 检查新增的单位
    new_units = visible_unit_ids - current_units
    for unit_id in new_units:
        unit = next(unit for unit in visible_units if unit.actor_id == unit_id)
        print(f"新增敌方单位：ID={unit.actor_id}, 类型={unit.type}, 位置=({unit.position.x}, {unit.position.y})")

    # 检查减少的单位
    removed_units = current_units - visible_unit_ids
    for unit_id in removed_units:
        print(f"敌方单位消失：ID={unit_id}")

    # 更新当前单位集合
    current_units = visible_unit_ids

    # 等待片刻后重新查询
    time.sleep(0.5)
