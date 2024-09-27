import OpenRA_Copilot_Library as OpenRA
import time


def execute_commands():
    GAME_API = OpenRA.GameAPI("localhost")

    if GAME_API.able_to_produce("电厂"):
        p1 = GAME_API.produce_units("电厂", 1)
        GAME_API.wait(p1)

    if GAME_API.able_to_produce("兵营"):
        p2 = GAME_API.produce_units("兵营", 1)
        GAME_API.wait(p2)

    if GAME_API.able_to_produce("步兵"):
        p3 = GAME_API.produce_units("步兵", 5)
        p4 = GAME_API.produce_units("火箭筒兵", 2)
        GAME_API.wait(p3)
        GAME_API.wait(p4)

    GAME_API.produce_units("矿场", 1)

    infantry = GAME_API.query_actor(
        TargetsQueryParam(type=["步兵"], faction="自己"))
    rocket_soldiers = GAME_API.query_actor(
        TargetsQueryParam(type=["火箭筒兵"], faction="自己"))
    enemy_base = GAME_API.query_actor(
        TargetsQueryParam(type=["基地"], faction="敌方"))[0]
    base_position = enemy_base.position
    units_to_attack = infantry + rocket_soldiers
    GAME_API.move_units_by_location(units_to_attack, base_position, attackmove=True)


if __name__ == "__main__":
    execute_commands()
