# 这个是一个示例文件，展示了如何使用OpenRA_Copilot_Library库，尽可能详细的包含了库中的所有功能，可以作为参考

# 该代码对应指令为：展开基地车，造一些步兵编成组1去探索，再补矿场，车间，来几个防空车编成组2和组3两路迂回到敌方基地，遇见步兵优先打步兵，并尝试进攻敌方基地，打不过就撤退，没血的车可以修一下，摄像机跟随组2防空车

import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import *
import time
import random
import threading

api = OpenRA.GameAPI("localhost")

# 1. 展开基地车

api.deploy_mcv_and_wait(wait_time=1.0)
print("基地车已展开完毕")


# 2. 确保能生产“步兵”，然后生产一些

if api.ensure_can_produce_unit("步兵"):
    print("可以生产步兵了，生产3个步兵中...")
    p = api.produce("步兵", 3)
    if p:
        api.wait(p)
        print("步兵生产完成")
else:
    print("无法生产步兵，可能资源不足或其它未知原因")


# 3. 步兵编成组1去探索周边地图
def explore_with_infantry(api):
    infantry_list = api.query_actor(TargetsQueryParam(type=["步兵"], faction="自己"))
    if infantry_list:
        api.form_group(infantry_list, group_id=1)
        FirstTime = True
        while True:
            map_data = api.map_query()
            for infantry in infantry_list:
                if not api.update_actor(infantry):
                    print(f"步兵({infantry.actor_id})已被消灭")
                    infantry_list.remove(infantry)
            if not infantry_list:
                print("所有步兵都已被消灭")
                break
            # 第一次可以适当扩大范围，比如 8 格，否则 5 格
            search_range = 10 if FirstTime else 5
            unexplored = api.get_unexplored_nearby_positions(map_data, infantry_list[0].position, search_range)
            FirstTime = False
            # 如果找不到，再试大一点
            if not unexplored:
                unexplored = api.get_unexplored_nearby_positions(map_data, infantry_list[0].position, search_range * 2)
            if not unexplored:
                print("附近都探索完了")
                break

            target_loc = random.choice(unexplored)
            print(f"前往({target_loc.x},{target_loc.y})...")
            arrived = api.move_units_by_location_and_wait(infantry_list, target_loc, max_wait_time=10.0, tolerance_dis=2)
            if not arrived:
                print("步兵似乎在路途中卡住了，再换个位置试试")
                continue
            time.sleep(0.5)

# 开启一个线程来探索，因为这个过程可能不会结束，或者持续很久
explore_thread = threading.Thread(target=explore_with_infantry, args=(api,))
explore_thread.start()

# 4. 建造“矿场”、“车间”以便生产载具

api.ensure_can_build_wait("矿场")
api.produce("矿场", 1)
api.ensure_can_build_wait("车间")
api.produce("车间", 1)

# 确保一下还有电
playerinfo = api.player_base_info_query()

while playerinfo.Power <= 0:
    if api.able_to_produce("核电厂"):
        p1 = api.produce("核电厂", 1)
    else:
        p1 = api.produce("电厂", 1)
    api.wait(p1)
    time.sleep(0.5)
    playerinfo = api.player_base_info_query()

# 5. 生产4个防空车

if api.ensure_can_produce_unit("防空车"):
    print("开始生产4辆防空车...")
    wtank = api.produce("防空车", 4)
    if wtank:
        api.wait(wtank, maxWaitTime=30)
        print("防空车已生产完毕")
else:
    print("无法生产防空车")


# 6. 防空车进攻敌方基地

ftrks = api.query_actor(TargetsQueryParam(type=["防空车"], faction="自己"))
enemy_bases = api.query_actor(TargetsQueryParam(type=["基地"], faction="敌方"))
if not enemy_bases:
    raise RuntimeError("未找到敌方基地")
enemy_base = enemy_bases[0]
base_position = enemy_base.position

midpoint = len(ftrks) // 2
team_2 = ftrks[:midpoint]
team_3 = ftrks[midpoint:]
api.form_group(team_2, group_id=2)
api.form_group(team_3, group_id=3)

path1 = api.find_path(team_2, base_position, '左侧路径')
path2 = api.find_path(team_3, base_position, '右侧路径')

print("编组2开始沿路径移动")
api.move_units_by_path(team_2, path1)
# 稍微等一下
time.sleep(1)
print("编组3开始沿路径移动")
api.move_units_by_path(team_3, path2)

active_units = list(team_2 + team_3)
start_time = time.time()
while active_units:
    if not api.update_actor(enemy_base):
        print(f"地方基地 {enemy_base.actor_id} 已被摧毁，完成目标！")
        break
    camera_moved = False
    if time.time() - start_time > 10:
        # 已经过了10s，摄像机可以不再跟随防空车
        camera_moved = True
    for unit in active_units:
        if not api.update_actor(unit):
            print(f"单位 {unit.actor_id} 已被摧毁")
            active_units.remove(unit)
            continue
        if unit.hppercent < 30:
            print(f"单位 {unit.actor_id} 血量不足，回基地修理")
            api.repair_units([unit])
            active_units.remove(unit)
            continue
        if not camera_moved and unit in team_2:
            api.move_camera_to(unit)
            camera_moved = True
        # 优先打步兵
        current_position = unit.position
        near_ememies = api.query_actor(TargetsQueryParam(type=["士兵"], faction="敌方", location=current_position, restrain=[{"distance": 6},{"visible": True}]))
        if near_ememies:
            for enemy in near_ememies:
                if api.can_attack_target(unit, enemy):
                    api.attack_target(unit, enemy_base)
                    continue

        # 尝试进攻敌方基地
        if api.can_attack_target(unit, enemy_base):
            api.attack_target(unit, enemy_base)
            continue

        # 否则向敌方基地移动
        api.move_units_by_location([unit],base_position)

    time.sleep(0.5)
