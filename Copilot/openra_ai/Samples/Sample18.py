# 该代码对应指令为：测试建造队列相关API
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam
import time

api = OpenRA.GameAPI("localhost")

# 1. 首先确保有电厂和兵营
mcv = api.query_actor(TargetsQueryParam(type=['mcv'], faction='自己'))
if mcv:
    # 如果找到基地车，展开它
    print("找到基地车，正在展开...")
    api.deploy_units([mcv[0]])
    time.sleep(0.5)

# 确保有电厂和兵营
print("确保有电厂和兵营...")
if not api.ensure_can_build_wait("电厂"):
    print("警告：无法建造电厂，可能已经存在")
if not api.ensure_can_build_wait("兵营"):
    print("警告：无法建造兵营，可能已经存在")

# 2. 测试查询生产队列
print("\n测试查询生产队列...")
building_queue = api.query_production_queue("Building")
print(f"建筑队列信息: {building_queue}")

# 3. 测试生产队列管理
print("\n测试生产队列管理...")
# 获取兵营
barracks = api.query_actor(TargetsQueryParam(type=["兵营"], faction="自己"))
if not barracks:
    print("警告：未找到兵营，跳过后续测试")
    exit()

# 开始生产步兵
print("开始生产步兵...")
api.produce("步兵", 3)

# 查询步兵队列
infantry_queue = api.query_production_queue("Infantry")
print(f"步兵队列信息: {infantry_queue}")

# 暂停生产
print("\n暂停生产...")
api.manage_production(barracks[0], "pause", "Infantry")
time.sleep(1)
infantry_queue = api.query_production_queue("Infantry")
print(f"暂停后的队列信息: {infantry_queue}")

# 继续生产
print("\n继续生产...")
api.manage_production(barracks[0], "resume", "Infantry")
time.sleep(1)
infantry_queue = api.query_production_queue("Infantry")
print(f"继续后的队列信息: {infantry_queue}")

# 4. 测试放置建筑
print("\n测试放置建筑...")
# 开始生产矿场
print("开始生产矿场...")
api.produce("矿场", 1)
time.sleep(2)  # 等待生产完成

# 获取生产完成的矿场
building_queue = api.query_production_queue("Building")
if building_queue.get("has_ready_item"):
    print("找到已就绪的建筑，尝试放置...")
    # 在兵营旁边放置
    placement_location = OpenRA.Location(
        barracks[0].position.x + 2,
        barracks[0].position.y
    )
    api.place_building(barracks[0], placement_location)
    print(f"建筑已放置在位置: {placement_location}")
else:
    print("没有找到已就绪的建筑")

# 5. 测试取消生产
print("\n测试取消生产...")
# 开始生产新的建筑
api.produce("雷达", 1)
time.sleep(1)
print("取消生产...")
api.manage_production(barracks[0], "cancel", "Building")
building_queue = api.query_production_queue("Building")
print(f"取消后的队列信息: {building_queue}")

print("\n测试完成!")