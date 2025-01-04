import socket
import json
import time
from typing import List, Optional
from .models import *


class GameAPI:
    def __init__(self, host, port=7445, cache_duration=60):
        self.server_address = (host, port)

    #通过socket和Game交互，发送信息，返回值为json结构
    def _send_request(self, command, data):

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
        data = {"location": location.to_dict()}
        return self._send_request('camera_move', data)

    # 向某个方向移动相机，必须满足 direction ∈ {ALL_DIRECTIONS}，如果不在范围内请转换到范围呢
    def move_camera_by_direction(self, direction: str, distance):
        data = {"direction": direction, "distance": distance}
        return self._send_request('camera_move', data)

    # 必须满足 unit_type ∈ {ALL_UNITS}，如果不在范围内请转换到范围呢
    def able_to_produce(self, unit_type: str):
        data = {"units": [{"unit_type": unit_type}]}
        response = self._send_request('query_produce_info', data)
        if response is not None and "canProduce" in response:
            return response["canProduce"]
        return False

    # 必须满足 unit_type ∈ {ALL_UNITS}，如果不在范围内请转换到范围呢
    # 返回值为waitId，可以通过waitId查询生产是否完成
    def produce_units(self, unit_type: str, quantity: int):
        data = {"units": [{"unit_type": unit_type, "quantity": quantity}]}
        response = self._send_request('start_production', data)
        try:
            if response is not None:
                return response["waitId"]
        except:
            print("Error in produce_units ,Response:")
            print(response)

    # 传入waitId，可以查询这个等待事件是否完成，返回值为bool
    # 目前只有生产
    def is_ready(self, waitId: int):
        data = {"waitId": waitId}
        response = self._send_request('query_wait_info', data)
        return response["status"]

    def wait(self, waitId: int, maxWaitTime: float = 20.0):
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
        data = {"targets": query_params.to_dict()}
        return self._send_request('select_unit', data)

    def form_group(self, actors, group_id):
        data = {
            "targets": {"actorId": [actor.actor_id for actor in actors]},
            "groupId": group_id
        }
        return self._send_request('form_group', data)

    def form_group(self, actors, group_id):
        data = {
            "targets": {"actorId": [actor.actor_id for actor in actors]},
            "groupId": group_id
        }
        return self._send_request('form_group', data)

    def query_actor(self, query_params):
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
                position = Location(data["position"]["x"], data["position"]["y"])
                actor.update_details(data["type"], data["faction"], position)
                actors.append(actor)
        except:
            print("Error in Query Actor ,Response:")
            print(response)

        return actors

    def find_path(self, actors, destination, method):
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
        a = Actor(actor_id)
        if self.update_actor(a):
            return a
        return None

    def update_actor(self, actor) -> bool:
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


    def deploy_units(self, actors: List[Actor]) -> Optional[int]:
        data = {"targets": {"actorId": [actor.actor_id for actor in actors]}}
        response = self._send_request('deploy', data)
        return response.get('waitId') if response else None


    def move_camera_to(self, actor: Actor) -> dict:
        data = {"actorId": actor.actor_id}
        return self._send_request('view', data)

    #占领
    def occupy_units(self, occupiers: List[Actor], targets: List[Actor]) -> dict:
        data = {
            "occupiers": {"actorId": [actor.actor_id for actor in occupiers]},
            "targets": {"actorId": [target.actor_id for target in targets]}
        }
        return self._send_request('occupy', data)

    #攻击指令，攻击移动，只会攻击路径旁的战斗单位，不会攻击建筑，因此攻击建筑，或者具体指定攻击某个人，需要用这个，但目标必须是我当前可见的Actor
    def attack_target(self, attacker: Actor, target: Actor) -> bool:
        data = {
            "attackers": {"actorId": [attacker.actor_id]},
            "targets": {"actorId": [target.actor_id] }
        }
        try:
            self._send_request('attack', data)
            return True
        except:
            return False

    # 修复车辆或建筑，都可以使用这个修复
    def repair_units(self, actors: List[Actor]) -> Optional[int]:
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
            ScreenMin=Location(response['ScreenMin']['X'], response['ScreenMin']['Y']),
            ScreenMax=Location(response['ScreenMax']['X'], response['ScreenMax']['Y']),
            IsMouseOnScreen=response.get('IsMouseOnScreen', False),
            MousePosition=Location(response['MousePosition']['X'], response['MousePosition']['Y'])
        )

