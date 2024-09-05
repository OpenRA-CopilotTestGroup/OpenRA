import OpenRA_Copilot_Library as OpenRA


def execute_commands():
    api = OpenRA.GameAPI("localhost")
    s1 = api.able_to_produce("步兵")
    print(s1)
    p3 = api.produce_units("步兵", 1)
    print(p3)

if __name__ == "__main__":
    execute_commands()
