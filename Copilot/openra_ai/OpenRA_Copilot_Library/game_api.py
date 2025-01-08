import socket
import json
import time
from typing import List, Optional
from .models import *


class GameAPI:
    def __init__(self, host, port=7445, cache_duration=60):
        # Initialize the GameAPI with server address and establish a socket connection
        self.server_address = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.server_address)

    def close(self):
        # Close the socket connection
        if self.sock:
            self.sock.close()
            self.sock = None

    # Send a request to the game server and return the response as a JSON object
    def _send_request(self, command, data):

        def receive_data(sock):
            # Helper function to receive data from the socket
            chunks = []
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
            return b''.join(chunks).decode('utf-8')

        data['command'] = command
        json_data = json.dumps(data)
        try:
            # Send the JSON data to the server
            self.sock.sendall(json_data.encode('utf-8'))
            # Receive the response from the server
            response = receive_data(self.sock)
            # Parse the response as JSON
            res_json = json.loads(response)
            if res_json["status"] < 0:
                print("\nError:Response ErrorCode :" + str(res_json["status"]))
                print("Response:\n"+response)
            return res_json
        except json.JSONDecodeError:
            print("Error:Response is Not Json.\nResponse:\n"+response)
            return None
        except Exception as e:
            print(f"Error in _send_request: {e}")
            return None

    def move_camera_by_location(self, location):
        # Move the camera to a specific location
        data = {"location": location.to_dict()}
        return self._send_request('camera_move', data)

    def move_camera_by_direction(self, direction: str, distance):
        # Move the camera in a specified direction by a certain distance
        data = {"direction": direction, "distance": distance}
        return self._send_request('camera_move', data)

    def able_to_produce(self, unit_type: str):
        # Check if a unit of a specific type can be produced
        data = {"units": [{"unit_type": unit_type}]}
        response = self._send_request('query_produce_info', data)
        if response is not None and "canProduce" in response:
            return response["canProduce"]
        return False

    def produce_units(self, unit_type: str, quantity: int):
        # Start production of a specified quantity of units of a given type
        data = {"units": [{"unit_type": unit_type, "quantity": quantity}]}
        response = self._send_request('start_production', data)
        try:
            if response is not None:
                return response["waitId"]
        except:
            print("Error in produce_units ,Response:")
            print(response)

    def is_ready(self, waitId: int):
        # Check if a production or wait event is complete
        data = {"waitId": waitId}
        response = self._send_request('query_wait_info', data)
        return response["status"]

    def wait(self, waitId: int, maxWaitTime: float = 20.0):
        # Wait for a production or wait event to complete, with a maximum wait time
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
        # Move units to a specific location, optionally using attack move
        data = {
            "targets": {"actorId": [actor.actor_id for actor in actors]},
            "location": location.to_dict(),
            "isAttackMove": 1 if attackmove else 0
        }
        return self._send_request('move_actor', data)

    def move_units_by_direction(self, actors, direction, distance):
        # Move units in a specified direction by a certain distance
        data = {
            "targets": {"actorId": [actor.actor_id for actor in actors]},
            "direction": direction,
            "distance": distance
        }
        return self._send_request('move_actor', data)

    def move_units_by_path(self, actors, path: list[Location]):
        # Move units along a specified path
        if not path:
            return
        data = {
            "targets": {"actorId": [actor.actor_id for actor in actors]},
            "path": [point.to_dict() for point in path]
        }
        return self._send_request('move_actor', data)

    def select_units(self, query_params):
        # Select units based on query parameters
        data = {"targets": query_params.to_dict()}
        return self._send_request('select_unit', data)

    def form_group(self, actors, group_id):
        # Form a group with specified actors and group ID
        data = {
            "targets": {"actorId": [actor.actor_id for actor in actors]},
            "groupId": group_id
        }
        return self._send_request('form_group', data)

    def query_actor(self, query_params):
        # Query information about actors based on query parameters
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
        # Find a path for actors to a destination using a specified method
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
        # Retrieve an actor by ID and update its details
        a = Actor(actor_id)
        if self.update_actor(a):
            return a
        return None

    def update_actor(self, actor) -> bool:
        # Update the details of an actor
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
        # Deploy units and return a wait ID if successful
        data = {"targets": {"actorId": [actor.actor_id for actor in actors]}}
        response = self._send_request('deploy', data)
        return response.get('waitId') if response else None

    def move_camera_to(self, actor: Actor) -> dict:
        # Move the camera to focus on a specific actor
        data = {"actorId": actor.actor_id}
        return self._send_request('view', data)

    def occupy_units(self, occupiers: List[Actor], targets: List[Actor]) -> dict:
        # Occupy target units with specified occupiers
        data = {
            "occupiers": {"actorId": [actor.actor_id for actor in occupiers]},
            "targets": {"actorId": [target.actor_id for target in targets]}
        }
        return self._send_request('occupy', data)

    def attack_target(self, attacker: Actor, target: Actor) -> bool:
        # Command an actor to attack a target
        data = {
            "attackers": {"actorId": [attacker.actor_id]},
            "targets": {"actorId": [target.actor_id] }
        }
        try:
            self._send_request('attack', data)
            return True
        except:
            return False

    def repair_units(self, actors: List[Actor]) -> Optional[int]:
        # Repair specified units
        data = {"targets": {"actorId": [actor.actor_id for actor in actors]}}
        return self._send_request('repair', data)

    def stop(self, actors: List[Actor]) -> dict:
        # Stop specified units
        data = {"targets": {"actorId": [actor.actor_id for actor in actors]}}
        return self._send_request('stop', data)

    def visible_query(self, location: Location) -> bool:
        # Query if a location is visible
        data = {"location": location.to_dict()}
        response = self._send_request('fog_query', data)
        return response.get('IsVisible', False) if response else False

    def explorer_query(self, location: Location) -> bool:
        # Query if a location has been explored
        data = {"location": location.to_dict()}
        response = self._send_request('fog_query', data)
        return response.get('IsExplored', False) if response else False

    def unit_range_query(self, actors: List[Actor]) -> List[int]:
        # Get all targets within the attack range of specified units
        data = {"targets": {"actorId": [actor.actor_id for actor in actors]}}
        response = self._send_request('unit_range_query', data)
        return response.get('actors', []) if response else []

    def unit_attribute_query(self, actors: List[Actor]) -> dict:
        # Query attributes of specified units
        data = {"targets": {"actorId": [actor.actor_id for actor in actors]}}
        return self._send_request('unit_attribute_query', data)

    def map_query(self) -> MapQueryResult:
        # Query the map information
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
        # Query the player's base information
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

    def screen_info_query(self) -> ScreenInfoResult:
        # Query the current screen information
        response = self._send_request('screen_info_query', {})
        if not response:
            raise ValueError("Failed to retrieve screen info data.")

        return ScreenInfoResult(
            ScreenMin=Location(response['ScreenMin']['X'], response['ScreenMin']['Y']),
            ScreenMax=Location(response['ScreenMax']['X'], response['ScreenMax']['Y']),
            IsMouseOnScreen=response.get('IsMouseOnScreen', False),
            MousePosition=Location(response['MousePosition']['X'], response['MousePosition']['Y'])
        )

