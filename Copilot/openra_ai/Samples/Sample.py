# COPILOT_PROMPT_IGNORE
# 这个是临时测试代码
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam
from OpenRA_Copilot_Library import Location
import time
import threading
# 创建GameAPI实例
api = OpenRA.GameAPI("localhost")

# 确保车间建成，开始生产防空车
api.ensure_building_wait("车间")

# 确保可以生产防空车
if api.ensure_can_produce_unit("防空车"):
    print("正在生产3辆防空车...")
    p = api.produce_units("防空车", 3)
    if p:
        api.wait(p)
        print("防空车生产完成")
else:
    raise RuntimeError("无法生产防空车")

# 防空车进行地图探索
def explore_with_anti_air_vehicles(api):
    aa_vehicles = api.query_actor(TargetsQueryParam(type=["防空车"], faction="己方"))
    if aa_vehicles:
        api.form_group(aa_vehicles, group_id=2)
        FirstTime = True
        while True:
            map_data = api.map_query()
            for vehicle in aa_vehicles:
                if not api.update_actor(vehicle):
                    print(f"防空车({vehicle.actor_id})已被消灭")
                    aa_vehicles.remove(vehicle)
            if not aa_vehicles:
                print("所有防空车都已被消灭")
                break
            search_range = 10 if FirstTime else 5
            unexplored = api.get_unexplored_nearby_positions(map_data, aa_vehicles[0].position, search_range)
            FirstTime = False
            if not unexplored:
                unexplored = api.get_unexplored_nearby_positions(map_data, aa_vehicles[0].position, search_range * 2)
            if not unexplored:
                print("附近都探索完了")
                break

            target_loc = unexplored[0]
            print(f"防空车前往({target_loc.x},{target_loc.y})...")
            arrived = api.move_units_by_location_and_wait(aa_vehicles, target_loc, max_wait_time=10.0, tolerance_dis=2)
            if not arrived:
                print("防空车似乎在路途中卡住了，再换个位置试试")
                continue
            time.sleep(0.5)

# 开启一个线程来探索
explore_aa_thread = threading.Thread(target=explore_with_anti_air_vehicles, args=(api,))
explore_aa_thread.start()
