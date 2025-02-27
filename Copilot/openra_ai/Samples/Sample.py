# COPILOT_PROMPT_IGNORE
# 这个是临时测试代码
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam
from OpenRA_Copilot_Library import Location
import time
import threading
# 创建GameAPI实例
api = OpenRA.GameAPI("localhost")

screen_info = api.screen_info_query()
mouse_position = screen_info.MousePosition

# 查询所有战斗单位（排除非战斗单位，如矿车、基地车等）
query_params = TargetsQueryParam(
    type=['步兵', '导弹兵', '炮兵', '轻坦克', '重坦', '犀牛', 'V2', '猛犸', '磁能坦克', '特斯拉坦克', '地震车'],
    faction='己方'
)
battle_units = api.query_actor(query_params)

# 如果没有找到战斗单位，则什么也不做
if not battle_units:
    raise ValueError("未找到战斗单位。")

# 为这些战斗单位找到到目标的两条路径：左路和右路
left_path = api.find_path(battle_units, mouse_position, method="左路")
right_path = api.find_path(battle_units, mouse_position, method="右路")

# 把单位分成两组，分别采用不同路径移动进行夹击
half_point = len(battle_units) // 2
left_units = battle_units[:half_point]
right_units = battle_units[half_point:]

# 沿途攻击移动
if left_units:
    api.move_units_by_path(left_units, left_path)
if right_units:
    api.move_units_by_path(right_units, right_path)

# # 确保车间建成，开始生产防空车
# api.ensure_building_wait("车间")

# # 确保可以生产防空车
# if api.ensure_can_produce_unit("防空车"):
#     print("正在生产3辆防空车...")
#     p = api.produce_units("防空车", 3)
#     if p:
#         api.wait(p)
#         print("防空车生产完成")
# else:
#     raise RuntimeError("无法生产防空车")

# # 防空车进行地图探索
# def explore_with_anti_air_vehicles(api):
#     aa_vehicles = api.query_actor(TargetsQueryParam(type=["防空车"], faction="己方"))
#     if aa_vehicles:
#         api.form_group(aa_vehicles, group_id=2)
#         FirstTime = True
#         while True:
#             map_data = api.map_query()
#             for vehicle in aa_vehicles:
#                 if not api.update_actor(vehicle):
#                     print(f"防空车({vehicle.actor_id})已被消灭")
#                     aa_vehicles.remove(vehicle)
#             if not aa_vehicles:
#                 print("所有防空车都已被消灭")
#                 break
#             search_range = 10 if FirstTime else 5
#             unexplored = api.get_unexplored_nearby_positions(map_data, aa_vehicles[0].position, search_range)
#             FirstTime = False
#             if not unexplored:
#                 unexplored = api.get_unexplored_nearby_positions(map_data, aa_vehicles[0].position, search_range * 2)
#             if not unexplored:
#                 print("附近都探索完了")
#                 break

#             target_loc = unexplored[0]
#             print(f"防空车前往({target_loc.x},{target_loc.y})...")
#             arrived = api.move_units_by_location_and_wait(aa_vehicles, target_loc, max_wait_time=10.0, tolerance_dis=2)
#             if not arrived:
#                 print("防空车似乎在路途中卡住了，再换个位置试试")
#                 continue
#             time.sleep(0.5)

# # 开启一个线程来探索
# explore_aa_thread = threading.Thread(target=explore_with_anti_air_vehicles, args=(api,))
# explore_aa_thread.start()
