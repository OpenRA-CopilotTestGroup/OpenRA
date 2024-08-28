import OpenRA_Copilot_Library as OpenRA
import time


def execute_commands():
    api = OpenRA.GameAPI("localhost")

    # 先建造电厂
    p1 = api.produce_units("电厂", 1)
    api.wait(p1)
    # 轮询检查电厂是否建造完成
    # while True:
    #     if api.query_actor(OpenRA.TargetsQueryParam(type=["电厂"], faction="自己")):
    #         break
    #     time.sleep(2)

    # 建造兵营
    p2 = api.produce_units("兵营", 1)
    api.wait(p2)

    # 轮询检查兵营是否建造完成
    # while True:
    #     if api.query_actor(OpenRA.TargetsQueryParam(type=["兵营"], faction="自己")):
    #         break
    #     time.sleep(2)

    # 建造5个步兵
    p3 = api.produce_units("步兵", 5)
    # 建造2个火箭
    p4 = api.produce_units("火箭筒兵", 2)
    api.wait(p3)
    api.wait(p4)

    # 建造矿场
    p5 = api.produce_units("矿场", 1)

    # 等待步兵和火箭兵建造完成
    # while True:
    #     infantry = api.query_actor(OpenRA.TargetsQueryParam(type=["步兵"], faction="自己"))
    #     rocket_soldiers = api.query_actor(OpenRA.TargetsQueryParam(type=["火箭筒兵"], faction="自己"))
    #     if len(infantry) >= 5 and len(rocket_soldiers) >= 2:
    #         break
    #     time.sleep(2)
    infantry = api.query_actor(
        OpenRA.TargetsQueryParam(type=["步兵"], faction="自己"))
    rocket_soldiers = api.query_actor(
        OpenRA.TargetsQueryParam(type=["火箭筒兵"], faction="自己"))
    # 进攻敌方基地
    enemy_base = api.query_actor(
        OpenRA.TargetsQueryParam(type=["基地"], faction="敌方"))[0]
    base_position = enemy_base.position
    # `infantry` is a variable that stores the information about the infantry units
    units_to_attack = infantry + rocket_soldiers
    api.move_units_by_location(units_to_attack, base_position, attackmove=True)


if __name__ == "__main__":
    execute_commands()
