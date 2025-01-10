import socket
import json
import time
from typing import List, Optional
from .models import *


class GameAPI:
    '''游戏API接口类，用于与游戏服务器进行通信
    提供了一系列方法来与游戏服务器进行交互，包括单位移动、生产、查询等功能。
    所有的通信都是通过socket连接完成的。'''

    def __init__(self, host, port=7445):
        self.server_address = (host, port)
        '''初始化 GameAPI 类

        Args:
            host (str): 游戏服务器地址，本地就填"localhost"。
            port (int): 游戏服务器端口，默认为 7445。
        '''
    # 通过socket和Game交互，发送信息，返回值为json结构

    def _send_request(self, command, data):
        '''通过socket和Game交互，发送信息并接收响应

        Args:
            command (str): 要执行的命令
            data (dict): 命令相关的数据参数

        Returns:
            dict: 服务器返回的JSON响应数据
            None: 如果响应解析失败
        '''
        def receive_data(sock):
            chunks = []
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
            return b''.join(chunks).decode('utf-8')

        data['command'] = command
        json_data = json.dumps(data)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(self.server_address)
            sock.sendall(json_data.encode('utf-8'))
            response = receive_data(sock)
        try:
            res_json = json.loads(response)
            if res_json["status"] < 0:
                print("\nError:Response ErrorCode :" + str(res_json["status"]))
                print("Response:\n"+response)
            return res_json
        except json.JSONDecodeError:
            print("Error:Response is Not Json.\nResponse:\n"+response)
            return None

    def move_camera_by_location(self, location):
        '''根据给定的位置移动相机

        Args:
            location (Location): 要移动到的位置
        '''
        data = {"location": location.to_dict()}
        return self._send_request('camera_move', data)

    def move_camera_by_direction(self, direction: str, distance):
        '''向某个方向移动相机

        Args:
            direction (str): 移动的方向，必须在 {ALL_DIRECTIONS} 中
            distance (int): 移动的距离
        '''
        data = {"direction": direction, "distance": distance}
        return self._send_request('camera_move', data)

    def able_to_produce(self, unit_type: str):
        '''检查是否可以生产指定类型的单位

        Args:
            unit_type (str): 单位类型，必须在 {ALL_UNITS} 中

        Returns:
            bool: 是否可以生产
        '''
        data = {"units": [{"unit_type": unit_type}]}
        response = self._send_request('query_produce_info', data)
        if response is not None and "canProduce" in response:
            return response["canProduce"]
        return False

    def produce_units(self, unit_type: str, quantity: int):
        '''生产指定数量的单位

        Args:
            unit_type (str): 单位类型
            quantity (int): 生产数量

        Returns:
            int: 生产任务的 waitId
            None: 如果任务创建失败
        '''
        data = {"units": [{"unit_type": unit_type, "quantity": quantity}]}
        response = self._send_request('start_production', data)
        try:
            if response is not None:
                return response["waitId"]
        except:
            print("Error in produce_units ,Response:")
            print(response)

    def is_ready(self, waitId: int):
        '''检查生产任务是否完成

        Args:
            waitId (int): 生产任务的 ID

        Returns:
            bool: 是否完成
        '''
        data = {"waitId": waitId}
        response = self._send_request('query_wait_info', data)
        return response["status"]

    def wait(self, waitId: int, maxWaitTime: float = 20.0):
        '''等待生产任务完成

        Args:
            waitId (int): 生产任务的 ID
            maxWaitTime (float): 最大等待时间，默认为 20 秒

        Returns:
            bool: 是否成功完成等待（false表示超时）
        '''
        data = {"waitId": waitId}
        response = self._send_request('query_wait_info', data)
        waitTime = .0
        stepTime = 0.1
        try:
            while response["waitStatus"] != "success":
                time.sleep(stepTime)
                waitTime += stepTime
                response = self._send_request('query_wait_info', data)
                if waitTime > maxWaitTime:
                    return False
        except:
            print("Error in wait ,Response:")
            print(response)
            return True
        return True

    def move_units_by_location(self, actors, location, attackmove=False):
        data = {
            "targets": {"actorId": [actor.actor_id for actor in actors]},
            "location": location.to_dict(),
            "isAttackMove": 1 if attackmove else 0
        }
        return self._send_request('move_actor', data)

    def move_units_by_direction(self, actors, direction, distance):
        data = {
            "targets": {"actorId": [actor.actor_id for actor in actors]},
            "direction": direction,
            "distance": distance
        }
        return self._send_request('move_actor', data)

    def move_units_by_path(self, actors, path: list[Location]):
        if not path:
            return
        data = {
            "targets": {"actorId": [actor.actor_id for actor in actors]},
            "path": [point.to_dict() for point in path]
        }
        return self._send_request('move_actor', data)

    def select_units(self, query_params):
        '''选中符合条件的单位

        Args:
            query_params (TargetsQueryParam): 查询参数

        Returns:
            List[Actor]: 选择的单位列表
        '''
        data = {"targets": query_params.to_dict()}
        return self._send_request('select_unit', data)

    def form_group(self, actors, group_id):
        data = {
            "targets": {"actorId": [actor.actor_id for actor in actors]},
            "groupId": group_id
        }
        return self._send_request('form_group', data)

    def form_group(self, actors, group_id):
        '''将单位编成编组

        Args:
            actors (List[Actor]): 要分组的单位列表
            group_id (int): 群组 ID
        '''
        data = {
            "targets": {"actorId": [actor.actor_id for actor in actors]},
            "groupId": group_id
        }
        return self._send_request('form_group', data)

    def query_actor(self, query_params):
        '''查询符合条件的单位

        Args:
            query_params (TargetsQueryParam): 查询参数

        Returns:
            List[Actor]: 符合条件的单位列表
        '''
        data = {"targets": query_params.to_dict()}
        response = self._send_request('query_actor', data)
        actors = []
        if response is None:
            return actors
        actors_data = response.get("actors")
        if actors_data is None:
            return actors
        try:
            for data in actors_data:
                actor = Actor(data["id"])
                position = Location(
                    data["position"]["x"], data["position"]["y"])
                hppercent = data["hp"] * 100 // data["maxHp"]
                if data["maxHp"] <= 0:
                    hppercent = -1
                actor.update_details(
                    data["type"], data["faction"], position, hppercent)
                actors.append(actor)
        except:
            print("Error in Query Actor ,Response:")
            print(response)

        return actors

    def find_path(self, actors, destination, method):
        '''为Actor找到到目标的路径

        Args:
            actors (List[Actor]): 要移动的Actor列表
            destination (Location): 目标位置
            method (str): 寻路方法，必须在 {"最短路"，"左路"，"右路"} 中

        Returns:
            List[Location]: 路径点列表，第0个是目标点，最后一个是Actor当前位置，相邻的点都是八方向相连的点
        '''
        data = {
            "targets": {"actorId": [actor.actor_id for actor in actors]},
            "destination": destination.to_dict(),
            "method": method
        }
        response = self._send_request('query_path', data)
        try:
            path = [Location(step["x"], step["y"])
                    for step in response["path"]]
            return path
        except Exception as e:
            print("Error in Find Path ,Response:")
            print(response)
            print(e)
            return []

    def get_actor(self, actor_id):
        '''获取指定 ID 的Actor，这是根据ActorID获取Actor的接口，只有已知ActorID是才能调用这个接口

        Args:
            actor_id (int): Actor ID

        Returns:
            Actor: 对应的Actor
            None: 如果Actor不存在
        '''
        a = Actor(actor_id)
        if self.update_actor(a):
            return a
        return None

    def update_actor(self, actor) -> bool:
        '''更新Actor信息，如果时间改变了，需要调用这个来更新Actor的各种属性（位置等）。

        Args:
            actor (Actor): 要更新的Actor

        Returns:
            bool: 如果Actor已死，会返回false，否则返回true
        '''
        data = {"targets": {"actorId":  [actor.actor_id]}}
        response = self._send_request('query_actor', data)
        if response is None:
            return False
        try:
            position = Location(
                response["actors"][0]["position"]["x"], response["actors"][0]["position"]["y"])
            actor.update_details(
                response["actors"][0]["type"], response["actors"][0]["faction"], position)
            return True
        except:
            print("Error in Update Actor ,Response:")
            print(response)
            return False

    def deploy_units(self, actors: List[Actor]) -> dict:
        '''部署/展开 单位

        Args:
            actors (List[Actor]): 要部署/展开 的单位列表

        Returns:
            dict: 操作结果
        '''
        data = {"targets": {"actorId": [actor.actor_id for actor in actors]}}
        return self._send_request('deploy', data)

    def move_camera_to(self, actor: Actor) -> dict:
        data = {"actorId": actor.actor_id}
        return self._send_request('view', data)

    # 占领
    def occupy_units(self, occupiers: List[Actor], targets: List[Actor]) -> dict:
        data = {
            "occupiers": {"actorId": [actor.actor_id for actor in occupiers]},
            "targets": {"actorId": [target.actor_id for target in targets]}
        }
        return self._send_request('occupy', data)

    # 攻击指令，攻击移动，只会攻击路径旁的战斗单位，不会攻击建筑，因此攻击建筑，或者具体指定攻击某个人，需要用这个，但目标必须是我当前可见的Actor
    def attack_target(self, attacker: Actor, target: Actor) -> bool:
        '''攻击指定目标

        Args:
            attacker (Actor): 发起攻击的Actor
            target (Actor): 被攻击的目标

        Returns:
            bool: 是否成功发起攻击(如果目标不可见，或者不可达，或者攻击者已经死亡，都会返回false)
        '''
        data = {
            "attackers": {"actorId": [attacker.actor_id]},
            "targets": {"actorId": [target.actor_id]}
        }
        try:
            self._send_request('attack', data)
            return True
        except:
            return False

    def repair_units(self, actors: List[Actor]) -> Optional[int]:
        '''修复单位

        Args:
            actors (List[Actor]): 要修复的单位列表，可以是载具或者建筑，修理载具需要修建修理中心

        Returns:
            int: 修复任务的 ID
            None: 如果任务创建失败
        '''
        data = {"targets": {"actorId": [actor.actor_id for actor in actors]}}
        return self._send_request('repair', data)

    def stop(self, actors: List[Actor]) -> dict:
        data = {"targets": {"actorId": [actor.actor_id for actor in actors]}}
        return self._send_request('stop', data)

    def visible_query(self, location: Location) -> bool:
        data = {"location": location.to_dict()}
        response = self._send_request('fog_query', data)
        return response.get('IsVisible', False) if response else False

    def explorer_query(self, location: Location) -> bool:
        data = {"location": location.to_dict()}
        response = self._send_request('fog_query', data)
        return response.get('IsExplored', False) if response else False

    # 获取这些传入Actor攻击范围内的所有Target
    def unit_range_query(self, actors: List[Actor]) -> List[int]:
        data = {"targets": {"actorId": [actor.actor_id for actor in actors]}}
        response = self._send_request('unit_range_query', data)
        return response.get('actors', []) if response else []

    def unit_attribute_query(self, actors: List[Actor]) -> dict:
        data = {"targets": {"actorId": [actor.actor_id for actor in actors]}}
        return self._send_request('unit_attribute_query', data)

    def map_query(self) -> MapQueryResult:
        response = self._send_request('map_query', {})
        if not response:
            raise ValueError("Failed to retrieve map data.")

        return MapQueryResult(
            MapWidth=response.get('MapWidth', 0),
            MapHeight=response.get('MapHeight', 0),
            Height=response.get('Height', [[]]),
            IsVisible=response.get('IsVisible', [[]]),
            IsExplored=response.get('IsExplored', [[]]),
            Terrain=response.get('Terrain', [[]]),
            ResourcesType=response.get('ResourcesType', [[]]),
            Resources=response.get('Resources', [[]])
        )

    def player_base_info_query(self) -> PlayerBaseInfo:
        response = self._send_request('player_baseinfo_query', {})
        if not response:
            raise ValueError("Failed to retrieve player base information.")

        return PlayerBaseInfo(
            Cash=response.get('Cash', 0),
            Resources=response.get('Resources', 0),
            Power=response.get('Power', 0),
            PowerDrained=response.get('PowerDrained', 0),
            PowerProvided=response.get('PowerProvided', 0)
        )

    # 查询当前玩家看到的屏幕信息，非常关键的一个接口，可以用来判断屏幕上的Actor是否在屏幕上，以及鼠标位置
    def screen_info_query(self) -> ScreenInfoResult:
        response = self._send_request('screen_info_query', {})
        if not response:
            raise ValueError("Failed to retrieve screen info data.")

        return ScreenInfoResult(
            ScreenMin=Location(response['ScreenMin']
                               ['X'], response['ScreenMin']['Y']),
            ScreenMax=Location(response['ScreenMax']
                               ['X'], response['ScreenMax']['Y']),
            IsMouseOnScreen=response.get('IsMouseOnScreen', False),
            MousePosition=Location(
                response['MousePosition']['X'], response['MousePosition']['Y'])
        )
