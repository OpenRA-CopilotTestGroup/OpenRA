import OpenRA_Copilot_Library as OpenRA
import time

def lure_and_attack_sample():
    api = OpenRA.GameAPI("localhost")

    jeeps = api.query_actor(OpenRA.TargetsQueryParam(type=["防空车"], faction="自己"))
    rocket_soldiers = api.query_actor(OpenRA.TargetsQueryParam(type=["火箭筒"], faction="自己"))
    tanks = api.query_actor(OpenRA.TargetsQueryParam(type=["v2"], faction="自己"))

    jeep = jeeps[0]
    initial_position = jeep.position

    enemy_base = api.query_actor(OpenRA.TargetsQueryParam(type=["基地"], faction="敌方"))[0]
    base_position = enemy_base.position

    # 摩托车向敌方基地移动
    api.move_units_by_location([jeep], base_position)

    while True:
        api.update_actor(jeep)
        # 检测有没有碰到人
        enemies_near_motorcycle = api.query_actor(OpenRA.TargetsQueryParam(faction="敌方", location=jeep.position, restrain=[{"distance": 5}]))

        if enemies_near_motorcycle:
            # 有人就往初始位置跑
            retreat_path = api.find_path([jeep], initial_position, '最短路径')
            if retreat_path:
                intermediate_position = retreat_path[len(retreat_path) // 2]
                api.move_units_by_location([jeep], initial_position)

                # 然后火箭和坦克靠上去
                api.move_units_by_location(rocket_soldiers, intermediate_position)
                api.move_units_by_location(tanks, intermediate_position)

                # 等待敌人靠近
                # while True:
                #     enemies_still_near = api.query_actor(OpenRA.TargetsQueryParam(faction="敌方", location=intermediate_position, restrain=[{"distance": 25}]))
                #     if enemies_still_near:
                #         break
                #     time.sleep(1)

                # api.move_units_by_location(rocket_soldiers, enemies_near_motorcycle[0].position)
                # api.move_units_by_location(tanks, enemies_near_motorcycle[0].position)

                break

        time.sleep(2)

if __name__ == "__main__":
    lure_and_attack_sample()

