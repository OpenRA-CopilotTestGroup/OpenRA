# 该代码对应指令为：尝试建造一个猛犸坦克
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam

api = OpenRA.GameAPI("localhost")

# 猛犸坦克的制造依赖于科技中心，修理厂和雷达
# 猛犸坦克需要制造与车间，而车间依赖于矿场，矿场依赖于电厂
# 因此需要尝试补全依赖
while not api.able_to_produce("猛犸"):

    if not api.query_actor(OpenRA.TargetsQueryParam(type=["科技中心"], faction="自己")) and api.able_to_produce("科技中心"):
        p = api.produce_units("科技中心", 1)
        api.wait(p)
        continue
    if not api.query_actor(OpenRA.TargetsQueryParam(type=["修理厂"], faction="自己")) and api.able_to_produce("修理厂"):
        p = api.produce_units("修理厂", 1)
        api.wait(p)
        continue
    if not api.query_actor(OpenRA.TargetsQueryParam(type=["雷达"], faction="自己")) and api.able_to_produce("雷达"):
        p = api.produce_units("雷达", 1)
        api.wait(p)
        continue
    if not api.query_actor(OpenRA.TargetsQueryParam(type=["车间"], faction="自己")) and api.able_to_produce("车间"):
        p = api.produce_units("车间", 1)
        api.wait(p)
        continue
    if not api.query_actor(OpenRA.TargetsQueryParam(type=["矿场"], faction="自己")) and api.able_to_produce("矿场"):
        p = api.produce_units("矿场", 1)
        api.wait(p)
        continue
    if not api.query_actor(OpenRA.TargetsQueryParam(type=["电厂"], faction="自己")) and api.able_to_produce("电厂"):
        p = api.produce_units("电厂", 1)
        api.wait(p)
        continue

m = api.produce_units("猛犸", 1)
api.wait(m)
