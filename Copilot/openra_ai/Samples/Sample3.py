# 该代码对应指令为：第一组士兵和坦克两路夹击敌方基地
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam

api = OpenRA.GameAPI("localhost")
soldiers = api.query_actor(TargetsQueryParam(type=['士兵', '坦克'], group_id=[1]))
enemy_base = api.query_actor(TargetsQueryParam(type=['基地'], faction='敌方'))[0]
destination = enemy_base.position  # 直接使用位置类型
num_soldiers = len(soldiers)
# 将步兵分成两组
half_num = num_soldiers // 2
soldier1 = soldiers[:half_num]
soldier2 = soldiers[half_num:]
path1 = api.find_path(soldier1, destination, '左侧路径')
path2 = api.find_path(soldier2, destination, '右侧路径')
api.move_units_by_path(soldier1, path1)
api.move_units_by_path(soldier2, path2)
