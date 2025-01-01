# 该代码对应指令为：逐步补全所有建筑，并在过程中确保电力
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam

api = OpenRA.GameAPI("localhost")

# 想要补全的建筑列表及先后顺序，可以根据需要自行调整
building_order = [
    "电厂",
    "兵营",
    "矿场",
    "车间",
    "雷达",
    "修理厂",
    "科技中心",
    "机场",
    "狗屋",
    "核电厂"
]

def ensure_enough_power(target_building):
    """
    如果即将建造 target_building 时电力不足，则优先建造电厂类建筑。
    仅在必须时（Power < 0）补充，否则会浪费生产周期。
    """
    info = api.player_base_info_query()
    if info.Power < 0:  # 剩余电力不足
        # 如果能直接造核电厂，就造核电厂，否则先造电厂
        if api.able_to_produce("核电厂"):
            p = api.produce_units("核电厂", 1)
            api.wait(p)
        elif api.able_to_produce("电厂"):
            p = api.produce_units("电厂", 1)
            api.wait(p)
        else:
            pass  # 如果以上都不能生产，则先跳过（或raise）

def produce_building(building):
    """
    如果还没有建造 building，且能够生产，就执行建造并等待完成。
    """
    existing = api.query_actor(TargetsQueryParam(type=[building], faction="己方"))
    if existing:
        return  # 已存在此建筑，直接跳过
    if api.able_to_produce(building):
        p = api.produce_units(building, 1)
        api.wait(p)
    else:
        pass  # 缺少前置建筑或无法生产时，可选择报错或暂时跳过

for building in building_order:
    produce_building(building)
    ensure_enough_power(building)

