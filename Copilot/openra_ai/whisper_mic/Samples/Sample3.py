import OpenRA_Copilot_Library as OpenRA


def execute_commands():
    api = OpenRA.GameAPI("localhost")
    s1 = api.query_actor(OpenRA.TargetsQueryParam(type=["步兵"], faction="自己", restrain=[{"relativeDirection": "左上","maxNum" : 1}]))
    s2 = api.query_actor(OpenRA.TargetsQueryParam(type=["步兵"], faction="自己", restrain=[{"relativeDirection": "右上","maxNum" : 1}]))
    s3 = api.query_actor(OpenRA.TargetsQueryParam(type=["步兵"], faction="自己", restrain=[{"relativeDirection": "左下","maxNum" : 1}]))
    s4 = api.query_actor(OpenRA.TargetsQueryParam(type=["步兵"], faction="自己", restrain=[{"relativeDirection": "右下","maxNum" : 1}]))
    
    enemy_base = api.query_actor(OpenRA.TargetsQueryParam(type=["基地"], faction="敌方"))[0]
    base_position = enemy_base.position
    
    p1 = api.find_path(s1,base_position,"最短路")
    p2 = api.find_path(s2,base_position,"左路")
    p3 = api.find_path(s3,base_position,"右路")
    p4 = api.find_path(s4,base_position,"最短路")
    
    api.move_units_by_path(s1,p1)
    api.move_units_by_path(s2,p2)
    api.move_units_by_path(s3,p3)
    api.move_units_by_path(s4,p4)

if __name__ == "__main__":
    execute_commands()
