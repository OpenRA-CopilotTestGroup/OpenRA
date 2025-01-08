# 该代码对应指令为：展开基地车，然后来几个步兵
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam
import time

api = OpenRA.GameAPI("localhost")

mcv = api.query_actor(TargetsQueryParam(type=['mcv'], faction='自己'))
if not mcv:
    raise Exception("未找到己方MCV单位。")

# 展开基地车
api.deploy_units([mcv[0]])
# 展开基地车有可能要一点时间，小等一下
time.sleep(0.5)

#建造步兵需要兵营，兵营需要电厂
while not api.able_to_produce("步兵"):
    if not api.query_actor(OpenRA.TargetsQueryParam(type=["兵营"], faction="自己")) and api.able_to_produce("兵营"):
        p = api.produce_units("兵营", 1)
        api.wait(p)
        continue
    if not api.query_actor(OpenRA.TargetsQueryParam(type=["电厂"], faction="自己")) and api.able_to_produce("电厂"):
        p = api.produce_units("电厂", 1)
        api.wait(p)
        continue

#随便取个3个就行
p = api.produce_units("步兵", 3)
api.wait(p)

