# 该代码对应指令为：测试建造队列相关API
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam
import time
import json


def format_production_queue(queue_info):
    """格式化生产队列信息，使其更易读"""
    if not queue_info:
        return "队列为空"

    status_map = {
        "completed": "已完成",
        "paused": "暂停中",
        "in_progress": "进行中",
        "waiting": "等待中"
    }

    result = []
    result.append(f"队列类型: {queue_info['queue_type']}")
    result.append(f"是否有就绪项目: {'是' if queue_info['has_ready_item'] else '否'}")
    result.append("\n队列项目:")

    for idx, item in enumerate(queue_info['queue_items'], 1):
        status = status_map.get(item['status'], "未知状态")
        progress = f"{item['progress_percent']}%" if not item['done'] else "100%"

        item_info = [
            f"  {idx}. {item['chineseName']} ({item['name']})",
            f"     状态: {status}",
            f"     进度: {progress}",
            f"     剩余时间: {item['remaining_time']}/{item['total_time']}",
            f"     剩余成本: {item['remaining_cost']}/{item['total_cost']}",
            f"     所有者ID: {item['owner_actor_id']}"
        ]
        result.extend(item_info)

    return "\n".join(result)


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
if not api.query_actor(TargetsQueryParam(type=["电厂"], faction="自己")):
    api.produce("电厂", 1, True)
if not api.ensure_can_build_wait("兵营"):
    print("警告：无法建造兵营，可能已经存在")
if not api.query_actor(TargetsQueryParam(type=["兵营"], faction="自己")):
    api.produce("兵营", 1, True)

# 塞两个电厂
api.produce("电厂", 1)
api.produce("电厂", 1)

# 2. 测试查询生产队列
print("\n测试查询生产队列...")
building_queue = api.query_production_queue("Building")
print("建筑队列信息:")
print(format_production_queue(building_queue))

time.sleep(5)

# 检查是否有已完成的建筑需要放置
if building_queue.get("has_ready_item"):
    print("\n发现已完成的建筑，尝试放置...")
    try:
        # 使用Building队列类型，不指定位置，让服务器自动选择位置
        api.place_building("Building")
        print("建筑已放置")
    except Exception as e:
        print(f"放置建筑失败: {str(e)}")

# 3. 测试生产队列管理
print("\n测试生产队列管理...")
# 获取兵营
barracks = api.query_actor(TargetsQueryParam(type=["兵营"], faction="自己"))
if not barracks:
    print("警告：未找到兵营，跳过后续测试")
    exit()

# 开始生产步兵
print("开始生产步兵...")
api.produce("步兵", 10)

# 查询步兵队列
infantry_queue = api.query_production_queue("Infantry")
print("步兵队列信息:")
print(format_production_queue(infantry_queue))

# 暂停生产
print("\n暂停生产...")
api.manage_production("Infantry", "pause")
time.sleep(1)
infantry_queue = api.query_production_queue("Infantry")
print("暂停后的队列信息:")
print(format_production_queue(infantry_queue))
time.sleep(10)

# 继续生产
print("\n继续生产...")
api.manage_production("Infantry", "resume")
time.sleep(1)
infantry_queue = api.query_production_queue("Infantry")
print("继续后的队列信息:")
print(format_production_queue(infantry_queue))

# 4. 测试放置建筑
print("\n测试放置建筑...")

building_queue = api.query_production_queue("Building")
for idx, item in enumerate(building_queue['queue_items'], 1):
    api.manage_production("Building", "cancel")

# 开始生产矿场
print("开始生产矿场...")
api.produce("矿场", 1)
time.sleep(7)  # 等待生产完成

# 获取生产完成的矿场
building_queue = api.query_production_queue("Building")
if building_queue.get("has_ready_item"):
    print("找到已就绪的建筑，尝试放置...")
    # 在兵营旁边放置
    placement_location = OpenRA.Location(
        barracks[0].position.x + 2,
        barracks[0].position.y
    )
    api.place_building("Building", placement_location)
    print(f"建筑已放置在位置: {placement_location}")
else:
    print("没有找到已就绪的建筑")

# 5. 测试取消生产
print("\n测试取消生产...")
# 开始生产新的建筑
api.produce("雷达", 1)
time.sleep(1)
print("取消生产...")
api.manage_production("Building", "cancel")
building_queue = api.query_production_queue("Building")
print("取消后的队列信息:")
print(format_production_queue(building_queue))

print("\n测试完成!")
