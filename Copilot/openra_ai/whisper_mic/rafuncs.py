
import os
import yaml
import re
from typing import Optional, List, Dict, Any
import threading
import traceback
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam

# from openai import client
from openai import OpenAI
CLIENT = OpenAI()

def get_chat_completion(
    messages: list[dict[str, str]],
    model: str = "gpt-4o",
    max_tokens=1500,
    temperature=1.0,
    stop=None,
    tools=None,
    functions=None
) -> str:
    params = {
        'model': model,
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': temperature,
        'stop': stop,
        'tools': tools,
    }
    global CLIENT
    if functions:
        params['functions'] = functions
    try:
        completion = CLIENT.chat.completions.create(**params)
        return completion.choices[0].message
    except Exception as e:
        print(f'gpt completion fail with param: {params}')
        raise e


config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')

with open(config_path, 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)

ALL_ACTORS = config['ALL_ACTORS']
ALL_DIRECTIONS = config['ALL_DIRECTIONS']
ALL_GROUPS = config['ALL_GROUPS']
ALL_REGIONS = config['ALL_REGIONS']
ALL_RELATIVES = config['ALL_RELATIVES']
ALL_BUILDINGS = config['ALL_BUILDINGS']
ALL_DEFENSE_DEVICES = config['ALL_DEFENSE_DEVICES']
ALL_INFANTRIES = config['ALL_INFANTRIES']
ALL_TANKS = config['ALL_TANKS']

# 合并 ALL_MOVABLES 和 ALL_UNITS
ALL_MOVABLES = ALL_INFANTRIES + ALL_TANKS
ALL_UNITS = ALL_BUILDINGS + ALL_DEFENSE_DEVICES + ALL_MOVABLES

gamelib_dir =  os.path.abspath(os.path.join(os.path.dirname(__file__), '../OpenRA_Copilot_Library'))
api_path = os.path.join(gamelib_dir, 'game_api.py')
api_struct_path = os.path.join(gamelib_dir, 'models.py')
with open(api_path, 'r', encoding='utf-8') as file:
   api_content = file.read()
with open(api_struct_path, 'r', encoding='utf-8') as file:
   api_struct_content = file.read()

sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Samples'))
sample_code = ""
sample_index = 1

for filename in os.listdir(sample_dir):
    print(f"SampleFileName:{filename}")
    if filename.endswith('.py'):
        file_path = os.path.join(sample_dir, filename)


        with open(file_path, 'r', encoding='utf-8') as file:
            first_line = file.readline().strip()
            if first_line == "# COPILOT_PROMPT_IGNORE":
               print(f"Skipping {filename} due to ignore mark.")
               continue
            code_content = file.read()

        sample_code += f"{sample_index}. {filename}\n<code>{code_content}</code>\n\n"
        sample_index += 1

DRONE_STRATEGY_ASSISTANT_PROMPT = f"""
You are a strategic AI Commander for OpenRA (RedAlerts) game. we have a list of basic ops in openra python api.
Here is the List of Params:
ALL_ACTORS = {ALL_ACTORS}
ALL_DIRECTIONS = {ALL_DIRECTIONS}
ALL_GROUPS = {ALL_GROUPS}
ALL_REGIONS = {ALL_REGIONS}
ALL_RELATIVES = {ALL_RELATIVES}
ALL_BUILDINGS = {ALL_BUILDINGS}
ALL_UNITS = {ALL_UNITS}
The interface is listed as follows:
api_struct:
<code>
{api_struct_content}
</code>
api_define:
<code>
{api_content}
</code>
given a composite commands, try to generate python code with control structure and the composition of basic api ops listed above.
For the given composite commands,
If there are some typo in the command, try to correct it. If some command misses some information to generate correct basic api ops,
try to complement it with the context from previous commands. If the parameter is the api call has some requirements and the parameter does not meet the requirements,
convert the parameter to meet the requirements. If some parts does not reasonable reflect some basic api ops,
or do not mean to do something, ignore them and do not generate python code for that part. The generated code should consider the previous commands and codes running in the game.
It means the game status can be changed by previous commands and the execution of the codes.
But we should not generate code for previous commands. Only generate code for current command.
The generated code must be encapsulated in <code> and </code> tag pair. The generated code should be executable.
API can extract the code from the <code> tag and execute it. Try to make the code logic as much as simple and try to avoid use time.sleep to wait some action done.
Here is the list of examples:
{sample_code}
"""

# print(DRONE_STRATEGY_ASSISTANT_PROMPT)

# DRONE_STRATEGY_ASSISTANT_PROMPT = f"""
# You are a strategic AI Commander for OpenRA (RedAlerts) game. we have a list of basic ops in openra python api.
# The interface is listed as follows:
# <code>
# class Location:
#     def __init__(self, x: int, y: int):
#         # x is the horion offset in the map.
#         # y is the vertical offset in the map.
#         self.x = x
#         self.y = y

# # TargetsQueryParam is the class used for searching target by query params.
# class TargetsQueryParam:
#     # when construct the TargetQueryParam, The type should be a list or None. each element in the list is one of {ALL_UNITS}. otherwise, convert it to elements in the possible list.
#     # The faction should be None or one of {ALL_ACTORS}, otherwise convert it to the possible value.
#     # The group_id should be a list and each element in the list is one of  {ALL_GROUPS}, otherwise convert it to possible value.
#     # The direction should be None or one of {ALL_DIRECTIONS}, otherwise convert it to possible value.
#     def __init__(self, type: Optional[List[str]]=None, faction: Optional[str]=None, group_id: Optional[int]=None, restrain: Optional[Dict]=None, location: Optional[Location]=None, direction: Optional[str]=None, distance: Optional[int]=None):
#         # type is the list of {ALL_UNITS}, or None.
#         # faction is one of the {ALL_ACTORS}, or None
#         # group_id is  the list of {ALL_GROUPS}, or None
#         # direction is one of the {ALL_DIRECTIONS}, or None
#         self.type = type
#         self.faction = faction
#         self.group_id = group_id
#         self.restrain = restrain
#         self.location = location
#         self.direction = direction
#         self.distance = distance

# # Actor is the actor of the game. We have some caching mechanism to avoid duplicated queries.
# class Actor:
#     def __init__(self, actor_id: int):
#         # actor_id: int
#         self.actor_id = actor_id
#         self.type = None
#         self.faction = None
#         self.position = None

#     def update_details(self, type: List[str], faction: str, position: Location):
#         # type is the list of all {ALL_UNITS}
#         # factor is one of the {ALL_ACTORS}
#         self.type = type
#         self.faction = faction
#         self.position = position

# # GameAPI: interface class to interact between api and game.
# class GameAPI:
#     def move_camera_by_location(self, location: Location) -> None:
#         # 移动摄像头到指定位置. 实时操作，调用结束时操作已经完成
#         # location: Location, 目标位置

#     # when we call this api, direction should be one of the {ALL_DIRECTIONS}, otherewise convert it to possible value.
#     def move_camera_by_direction(self, direction: str, distance: int) -> None:
#         # 按方向和距离移动摄像头. 实时操作，调用结束时操作已经完成
#         # direction: str, 移动方向, one of the {ALL_DIRECTIONS}
#         # distance: int, 移动距离

#     # when we call this api, unit_type should be one of the {ALL_UNITS}, otherwise convert it to possible value.
#     def able_to_produce(self, unit_type: str) -> bool:
#         # 准备生产单位. 实时操作，调用结束时操作已经完成
#         # unit_type: str, 单位类型, one of the {ALL_UNITS}
#         # quantity: int, 生产数量
#         # Returns: bool, if ready to build that quantity of the unit_type.

#     # when we call this api, unit_type should be one of the {ALL_UNITS}, otherwise convert it to possible value.
#     def produce_units(self, unit_type: str, quantity: int) -> int:
#         # 生产单位. 异步操作，会返回action_id. api可以调用wait(action_id) 等待操作完成。
#         # unit_type: str, 单位类型, one of the {ALL_UNITS}
#         # quantity: int, 生产数量
#         # Returns: int, operation id, used in waiting operation is done.

#     def is_ready(self, waitId: Optional[int]) -> bool:
#         # 检查waitId对应的异步操作是否完成
#         # waitId: Optional[int], the waitId returned from previous async call like produce_units or move_units_by_location. None means previous action do not generate waitId.
#         # Returns: bool, True is is done, else False.

#     def wait(self, waitId: Optional[int]) -> bool:
#         # 等待waitId对应的异步操作完成.
#         # waitId: int, thewaitId returned from previous async call like produce_units or move_units_by_location. None means previous action do not generate waitId.
#         # Returns: bool, True is is wait success, else False.

#     def move_units_by_location(self, actors: List[Actor], location: Location, attackmove: bool=False) -> None:
#         # 移动单位到指定位置. 异步操作，会返回action_id. api可以调用wait(action_id) 等待操作完成。
#         # actors: List[Actor], 需要移动的实体列表
#         # location: Location, 目标位置
#         # attack: bool, 是否攻击目标

#     def move_units_by_direction(self, actors: List[Actor], direction: str, distance: int) -> None:
#         # 按方向和距离移动单位. 异步操作，会返回action_id. api可以调用wait(action_id) 等待操作完成。
#         # actors: List[Actor], 需要移动的实体列表
#         # direction: str, 移动方向, one of the {ALL_DIRECTIONS}
#         # distance: int, 移动距离
#         # attack: bool, 是否攻击目标

#     def move_units_by_path(self, actors: List[Actor], path: List[Location]) -> None:
#         # 按路径移动单位. 异步操作，会返回action_id. api可以调用wait(action_id) 等待操作完成。
#         # actors: List[Actor], 需要移动的实体列表
#         # path: List[Location], 路径上的格子列表

#     # when we call this api, group_id should be one of the {ALL_GROUPS}, otherwise convert it to possible value.
#     def form_group(self, actors: List[Actor], group_id: int) -> None:
#         # 选择指定目标并编组. 实时操作，调用结束时操作已经完成
#         # actors: List[Actor], 实体列表
#         # group_id: int, 组ID, one of the {ALL_GROUPS}

#     # when we call this api, group_id should be one of the {ALL_GROUPS}, otherwise convert it to possible value.
#     def form_group(self, query_params: TargetsQueryParam, group_id: int) -> None:
#         # 选择指定目标并编组. 实时操作，调用结束时操作已经完成
#         # query_params: TargetssQueryParam, query params to select actors
#         # group_id: int, 组ID, one of the {ALL_GROUPS}

#     def select_units(self, query_params: TargetsQueryParam) -> List[Actor]:
#         # 选中符合条件的实体. 实时操作，调用结束时操作已经完成
#         # query_params: TargetsQueryParam, 目标查询参数
#         # Returns: list of Actors those meet the requirements.

#     def query_actor(self, query_params: TargetsQueryParam) -> List[Actor]:
#         # 查询符合条件的实体. 实时操作，调用结束时操作已经完成
#         # query_params: TargetsQueryParam, 目标查询参数
#         # Returns: list of Actors those meet the requirements.

#     def get_actor_details(self, actor_id: int) -> Actor:
#         # 获取实体的详细信息. 实时操作，调用结束时操作已经完成
#         # actor_id: int, 实体ID
#         # Returns: Actor that has the actor_id

#     def find_path(self, actors: List[Actor], destination: Location, method: str) -> List[Location]:
#         # 寻找actors移动到destination的路径。实时操作，调用结束时操作已经完成
#         # actors: List[Actor], 需要寻路的实体列表
#         # destination: Location, 寻路终点
#         # method: str
#         # Returns: list of Location that form the path to destination

#     def update_actor(self, actor: Actor) -> None:
#         # 更新actor状态
#         # actor: Actor with details.

# # Global variables:
# GAME_API = GameAPI("localhost")
# </code>


# given a composite commands, try to generate python code with control structure and the composition of basic api ops listed above.
# For the given composite commands,
# If there are some typo in the ommand, try to correct it. If some command misses some information to generate correct basic api ops,
# try to complement it with the context from previous commands. If the parameter is the api call has some requirements and the parameter does not meet the requirements,
# convert the parameter to meet the requirements. If some parts does not reasonable reflect some basic api ops,
# or do not mean to do something, ignore them and do not generate python code for that part. The generated code should consider the previous commands and codes running in the game.
# It means the game status can be changed by previous commands and the execution of the codes.
# But we should not generate code for previous commands. Only generate code for current command.
# The generated code must be encapsulated in <code> and </code> tag pair. The generated code should be executable.
# API can extract the code from the <code> tag and execute it. Try to make the code logic as much as simple and try to avoid use time.sleep to wait some action done.

# Here is the list of examples:

# Given input context is:
# 先建造一个电厂，再造一个兵营, 造5个步兵，两个火箭炮，补一个矿场。等造好步兵和火箭后，所有步兵和火箭攻击敌方基地。

# The expectd generated python code is wrapped with <code> and </code> tag pair as follows:
# <code>
# import OpenRA_Copilot_Library as OpenRA
# from OpenRA_Copilot_Library import TargetsQueryParam
# from openai import OpenAI

# GAME_API = OpenRA.GameAPI("localhost")

# if GAME_API.able_to_produce('电厂'):
#     p1 = GAME_API.produce_units('电厂', 1)
#     GAME_API.wait(p1)

# if GAME_API.able_to_produce('兵营'):
#     p2 = GAME_API.produce_units('兵营', 1)
#     GAME_API.wait(p2)

# if GAME_API.able_to_produce('步兵'):
#     p3 = GAME_API.produce_units('步兵', 5)
#     if GAME_API.able_to_produce('火箭筒'):
#         p4 = GAME_API.produce_units('火箭筒', 2)
#         GAME_API.wait(p4)
#     GAME_API.wait(p3)

# if GAME_API.able_to_produce('矿场'):
#     p5 = GAME_API.produce_units('矿场', 1)

# infantry = GAME_API.query_actor(TargetsQueryParam(type=['步兵'], faction='己方'))
# light_tanks = GAME_API.query_actor(TargetsQueryParam(type=['火箭筒'], faction='己方'))
# enemy_base = GAME_API.query_actor(TargetsQueryParam(type=['基地'], faction='敌方'))[0]
# base_position = enemy_base.position

# units_to_attack = infantry + light_tanks
# GAME_API.move_units_by_location(units_to_attack, base_position, attackmove=True)

# </code>

# Given input context is:
# 第一组士兵和坦克两路夹击敌方基地

# The expectd generated python code is wrapped with <code> and </code> tag pair as follows:
# <code>
# soldiers = GAME_API.query_actor(TargetsQueryParam(type=['士兵', '坦克'], group_id=[1]))
# enemy_base = GAME_API.query_actor(TargetsQueryParam(type=['基地'], faction='敌方'))[0]
# destination = enemy_base.position  # 直接使用位置类型
# num_soldiers = len(soldiers)
# # 将步兵分成两组
# half_num = num_soldiers // 2
# soldier1 = soldiers[:half_num]
# soldier2 = soldiers[half_num:]
# path1 = GAME_API.find_path(soldier1, destination, '左侧路径')
# path2 = GAME_API.find_path(soldier2, destination, '右侧路径')
# GAME_API.move_units_by_path(soldier1, path1, attackmove=True)
# GAME_API.move_units_by_path(soldier2, path2, attackmove=True)
# </code>

# Given input context is:
# 先让防空车去敌方基地勾引一下，然后士兵和坦克一起迎上去打敌方基地

# The expectd generated python code is wrapped with <code> and </code> tag pair as follows:
# <code>
# motorcycles = GAME_API.query_actor(TargetsQueryParam(type=['防空车']))
# soldiers = GAME_API.query_actor(TargetsQueryParam(type=['士兵']))
# tanks = GAME_API.query_actor(TargetsQueryParam(type=['坦克']))
# enemy_base = GAME_API.query_actor(TargetsQueryParam(type=['基地'], faction='敌方'))[0]
# initial_position = motorcycles[0].position
# base_position = enemy_base.position
# # 轻坦向敌方基地移动
# action_id = GAME_API.move_units_by_location(motorcycles, base_position)
# GAME_API.wait(action_id)
# while True:
#     # 检测有没有碰到人
#     enemies_near_motorcycle = GAME_API.query_actor(TargetsQueryParam(faction='敌方', location=base_position, restrain=[{{'distance': 5}}]))
#     if enemies_near_motorcycle:
#         # 有人就往初始位置跑
#         retreat_path = GAME_API.find_path(motrocycles, initial_position, '最短路径')
#         if retreat_path:
#             intermediate_position = retreat_path[len(retreat_path) // 2]
#             GAME_API.move_units_by_location(motorcycles, intermediate_position)
#             # 然后步兵和轻坦靠上去
#             GAME_API.move_units_by_location(soldiers + tanks, intermediate_position)
#             # 等待敌人靠近
#             while not GAME_API.query_actor(TargetsQueryParam(faction='敌方', location=intermediate_position, restrain=[{{'distance': 2}}])):
#                 pass
#             GAME_API.move_units_by_location(soldiers + tanks, intermediate_position, attackmove=True)
#     break
# </code>

# Given input context is:
# 爆5个工程师，去上面把油井占了，用我家里那两个飞机护一下

# The expectd generated python code is wrapped with <code> and </code> tag pair as follows:
# <code>
# produce_id = GAME_API.produce_units("工程师", 5)
# GAME_API.wait(produce_id)
# home_base = GAME_API.query_actor(TargetsQueryParam(type=["基地"]))[0]
# home_position = home_base.position
# engineers = GAME_API.query_actor(TargetsQueryParam(type=["工程师"], location=home_position, restrain=[{{"relativeDirection": "附近", "maxNum": 5}}]))
# airplanes = GAME_API.query_actor(TargetsQueryParam(type=["飞机"], location=home_position, restrain=[{{"relativeDirection": "附近", "maxNum": 2}}]))
# oil_derricks = GAME_API.query_actor(TargetsQueryParam(type=["油井"], faction="中立", location=home_position, restrain=[{{"direction": "上", "distance": 50}}]))
# oil_derrick_position = oil_derricks[0].position
# # 抱团移动
# GAME_API.move_units_by_location(engineers, oil_derrick_position)
# GAME_API.move_units_by_location(airplanes, oil_derrick_position)
# # 只要有一个工程师到附近了，就开启后续占领逻辑
# while True:
#     nearest_engineer = min(
#         engineers,
#         key=lambda actor: (
#             (GAME_API.get_actor_details(actor.actor_id).position.x - oil_derrick_position.x) ** 2 +
#             (GAME_API.get_actor_details(actor.actor_id).position.y - oil_derrick_position.y) ** 2
#         ) ** 0.5
#     )
#     distance_to_oil_derrick = (
#         (nearest_engineer.position.x - oil_derrick_position.x) ** 2 +
#         (nearest_engineer.position.y - oil_derrick_position.y) ** 2
#     ) ** 0.5
#     if distance_to_oil_derrick < 5:  # 先随便写个5
#         break
# # 工程师分开占油井
# for engineer, oil_derrick in zip(engineers, oil_derricks):
#     GAME_API.move_units_by_location([engineer], oil_derrick.position)
#     # 多余的工程师回家
#     if len(engineers) > len(oil_derricks):
#         remaining_engineers = engineers[len(oil_derricks):]
#         GAME_API.move_units_by_location(remaining_engineers, home_position)
# </code>
# """

CACHED_PREVIOUS_PROMPTS = []
MAX_CACHED_PROMPTS = 0
CODE_REGEX = re.compile(r'<code>(.*)</code>', re.M | re.S)
CODE_REGEX2 = re.compile(r'```python(.*)```', re.M | re.S)
api = OpenRA.GameAPI("localhost")

def execute(command):
    try:
        if callable(command):
            command()
        else:
            exec(command)
    except Exception as e:
        traceback.print_tb(e.__traceback__)
        traceback.print_exc()
        print(f'failed to execute:\n`{command}\n`')


def handle_strategy_command(prompt=None, model="gpt-4o"):
    global DRONE_STRATEGY_ASSISTANT_PROMPT
    global CACHED_PREVIOUS_PROMPTS
    global MAX_CACHED_PROMPTS
    global DEFAULT_FUNCS
    global CODE_REGEX
    default_func = None
    if prompt is None:
        print('prompt should not be None')
        return
    messages = []
    messages.append({"role": "system", "content": DRONE_STRATEGY_ASSISTANT_PROMPT})
    for previous_prompt in CACHED_PREVIOUS_PROMPTS:
        messages.append(previous_prompt)
    messages.append({"role": "user", "content": prompt})
    # print(f'messages=\n{len(messages)}\n')
    completion = get_chat_completion(model=model, messages=messages, tools=None)
    print(f'command to execute:\n{completion.content}\n')
    code_match = CODE_REGEX.search(completion.content)
    if code_match:
        executable = code_match.group(1)
        print(f'executable={executable}')
        thread = threading.Thread(target=execute, args=(executable,))
        thread.start()
    else:
        code_match = CODE_REGEX2.search(completion.content)
        if code_match:
            executable = code_match.group(1)
            print(f'executable={executable}')
            thread = threading.Thread(target=execute, args=(executable,))
            thread.start()
        else:
            print(f'failed to find matched code\n{completion.content}\n')
    if len(CACHED_PREVIOUS_PROMPTS) >= MAX_CACHED_PROMPTS:
        if CACHED_PREVIOUS_PROMPTS:
            CACHED_PREVIOUS_PROMPTS.pop(0)
        if CACHED_PREVIOUS_PROMPTS:
            CACHED_PREVIOUS_PROMPTS.pop(0)
    if len(CACHED_PREVIOUS_PROMPTS) < MAX_CACHED_PROMPTS:
        CACHED_PREVIOUS_PROMPTS.append({"role": "user", "content": prompt})
        CACHED_PREVIOUS_PROMPTS.append({"role": "assistant", "content": completion.content})
