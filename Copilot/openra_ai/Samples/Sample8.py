#该代码对应指令为：派一个步兵探索一下地图
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import *
import random
import time

api = OpenRA.GameAPI("localhost")

infantry = api.query_actor(OpenRA.TargetsQueryParam(type=["步兵"], faction="自己"))[0]
current_position = infantry.position

MAX_MOVE_DISTANCE = 5

def get_unexplored_nearby_positions(map_query_result, current_pos, max_distance):
    neighbors = []
    for dx in range(-max_distance, max_distance + 1):
        for dy in range(-max_distance, max_distance + 1):
            if abs(dx) + abs(dy) > max_distance:
                continue
            if dx == 0 and dy == 0:
                continue
            x, y = current_pos.x + dx, current_pos.y + dy
            if 0 <= x < map_query_result.MapWidth and 0 <= y < map_query_result.MapHeight:
                if not map_query_result.IsExplored[x][y]:  # 未探索的区域
                    neighbors.append(Location(x, y))
    return neighbors

def move_soldier_to_location(infantry, target_position):
    last_position = None
    stuck_time = .0
    deltatime = 0.5
    api.move_units_by_location([infantry], target_position)
    while True:
        api.update_actor(infantry)
        current_position = infantry.position

        if current_position == target_position:
            return True
        if current_position == last_position:
            stuck_time += deltatime
        else:
            stuck_time = .0
        if stuck_time > 2.0:
            return False
        last_position = current_position
        time.sleep(deltatime)

FirstTime = True
while True:
    # 获取最新地图信息
    map_data = api.map_query()
    # 获取未探索的邻近区域
    unexplored_positions = get_unexplored_nearby_positions(map_data, current_position,MAX_MOVE_DISTANCE * 3 if FirstTime else MAX_MOVE_DISTANCE)
    #简单倍增一下，扩大范围
    if not unexplored_positions:
        unexplored_positions = get_unexplored_nearby_positions(map_data, current_position,MAX_MOVE_DISTANCE * 2)
    if not unexplored_positions:
        unexplored_positions = get_unexplored_nearby_positions(map_data, current_position,MAX_MOVE_DISTANCE * 4)
    FirstTime = False
    if not unexplored_positions:
        print("该士兵附近已探索完毕")
        break
    next_position = random.choice(unexplored_positions)
    if not move_soldier_to_location(infantry, next_position):
        print("士兵卡住了，重新选择目标位置")
        continue
    time.sleep(0.1)
