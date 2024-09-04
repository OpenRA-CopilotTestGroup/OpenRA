import OpenRA_Copilot_Library as OpenRA


def execute_commands():
    api = OpenRA.GameAPI("localhost")
    s1 = api.select_units(OpenRA.TargetsQueryParam(type=["士兵"], faction="自己"))

if __name__ == "__main__":
    execute_commands()
