# 该代码对应指令为：派一些工程师去占领一下左边的油井
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam, Location
import time

api = OpenRA.GameAPI("localhost")

screen = api.screen_info_query()
sc_middle = (screen.ScreenMin + screen.ScreenMax) // 2

# 查询地图上的油井位置
oil_refineries = api.query_actor(TargetsQueryParam(type=["油井"], faction="中立"))
if not oil_refineries:
    raise RuntimeError("地图上没有油井可供占领")

# 筛选右边的油井
right_oil_refineries = [
    refinery for refinery in oil_refineries if refinery.position.x < sc_middle.x
]
if not right_oil_refineries:
    raise RuntimeError("右边没有油井可供占领")

# 查询工程师单位
engineers = api.query_actor(TargetsQueryParam(type=["工程师"], faction="自己"))
needNum = len(right_oil_refineries)
if len(engineers) < needNum:
    p1 = api.produce_units("工程师", needNum - len(engineers))
    api.wait(p1)
    engineers = api.query_actor(TargetsQueryParam(type=["工程师"], faction="自己"))
else:
    engineers = engineers[:needNum]

# 分配工程师到每个油井
assignments = {}
available_engineers = engineers[:]

for oil_refinery in right_oil_refineries:
    if not available_engineers:
        raise RuntimeError("工程师数量不足，无法占领所有油井")
    engineer = available_engineers.pop(0)
    assignments[engineer] = oil_refinery

# 执行占领任务
for engineer, oil_refinery in assignments.items():
    print(f"派遣工程师 {engineer.actor_id} 去占领油井 {oil_refinery.actor_id}")
    api.move_units_by_location([engineer], oil_refinery.position)

while True:
    if not assignments:
        break
    for engineer, oil_refinery in assignments.items():
        if not api.update_actor(engineer):
            print(f"工程师 {engineer.actor_id} 被摧毁，无法完成占领任务")
            assignments.pop(engineer)
            continue
        if engineer.position.manhattan_distance(oil_refinery.position) <= 3:
            print(f"工程师 {engineer.actor_id} 到达油井 {oil_refinery.actor_id}，开始占领")
            api.occupy_units([engineer], [oil_refinery])
            assignments.pop(engineer)
            break
    time.sleep(1)

print("占领任务完成")