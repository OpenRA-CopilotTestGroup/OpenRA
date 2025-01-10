# 这个是一个示例文件，展示了如何使用OpenRA_Copilot_Library库，尽可能详细的包含了库中的所有功能，可以作为参考

# 该代码对应指令为：展开基地车，造一些步兵编成组1去探索，再补矿场，车间，来几个防空车编成组2和组3两路迂回到敌方基地，遇见步兵优先打步兵，并尝试进攻敌方基地，打不过就撤退，没血的车可以修一下，摄像机跟随组2防空车

import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import *
import time

api = OpenRA.GameAPI("localhost")


# 1. 查询本方玩家基础信息
player_info = api.player_base_info_query()
print("当前现金:", player_info.Cash, "  资源:", player_info.Resources, "  电力:", player_info.Power)

# 2. 找到尚未部署的基地车(MCV)，展开基地
mcv_units = api.query_actor(TargetsQueryParam(type="mcv"))  # 这里假设MCV是移动基地车的类型
if mcv_units:
    print("找到MCV, 正在展开基地...")
    api.deploy_units(mcv_units)
    time.sleep(1)  # 给点时间让动画完成

# todo..
