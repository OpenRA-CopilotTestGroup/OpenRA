import socket
import json
import time
from .models import Actor, Location, TargetsQueryParam

class GameAPI:
    def __init__(self, host, port = 7445, cache_duration=60):
        self.server_address = (host, port)
        self.actor_cache = {}
        self.cache_duration = cache_duration

    def _send_request(self, command, data):
        data['command'] = command
        json_data = json.dumps(data)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(self.server_address)
            sock.sendall(json_data.encode('utf-8'))
            response = sock.recv(4096).decode('utf-8')
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print("Error:Response is Not Json.\nResponse:\n"+response)
            return None

    def _cache_actor(self, actor):
        self.actor_cache[actor.actor_id] = {
            "actor": actor,
            "timestamp": time.time()
        }

    def _is_cache_valid(self, actor_id):
        if actor_id in self.actor_cache:
            cached_time = self.actor_cache[actor_id]["timestamp"]
            return (time.time() - cached_time) < self.cache_duration
        return False

    def move_camera_by_location(self, location):
        data = {"location": location.to_dict()}
        return self._send_request('camera_move', data)

    def move_camera_by_direction(self, direction, distance):
        data = {"direction": direction, "distance": distance}
        return self._send_request('camera_move', data)

    def produce_units(self, unit_type, quantity):
        data = {"units": [{"unit_type": unit_type, "quantity": quantity}]}
        return self._send_request('start_production', data)

    def move_units_by_location(self, actors, location):
        data = {
            "targets": {"actorId": [actor.actor_id for actor in actors]},
            "location": location.to_dict()
        }
        return self._send_request('move_actor', data)

    def move_units_by_direction(self, actors, direction, distance):
        data = {
            "targets": {"actorId": [actor.actor_id for actor in actors]},
            "direction": direction,
            "distance": distance
        }
        return self._send_request('move_actor', data)

    def move_units_by_path(self, actors, path_tiles):
        data = {
            "targets": {"actorId": [actor.actor_id for actor in actors]},
            "pathTiles": path_tiles
        }
        return self._send_request('move_actor_on_tile_path', data)

    def follow_camera(self, actors):
        data = {
            "targets": {"actorId": [actor.actor_id for actor in actors]}
        }
        return self._send_request('camera_follow', data)

    def select_units(self, query_params):
        data = {"targets": query_params.to_dict()}
        return self._send_request('select_unit', data)

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
        for data in actors_data:
            actor = Actor(data["Id"])
            position = Location(data["Position"]["X"], data["Position"]["Y"])
            actor.update_details(data["Type"], data["Faction"], position)
            actors.append(actor)
            self._cache_actor(actor)
        
        return actors

    def get_actor_details(self, actor_id):
        if self._is_cache_valid(actor_id):
            return self.actor_cache[actor_id]["actor"]

        response = self._send_request('query_actor', {"actorId": [actor_id]})
        actor_data = response["actors"][0]
        actor = Actor(actor_data["Id"])
        actor.update_details(actor_data["Type"], actor_data["Faction"], actor_data["Position"])
        self._cache_actor(actor)
        return actor

    def query_tile_info(self, compress_num=5, actors=None):
        data = {"compressNum": compress_num}
        if actors:
            data["targets"] = {"actorId": [actor.actor_id for actor in actors]}
        return self._send_request('query_tile', data)

    def query_tile_move(self, actors, compress_num=5, path_tiles=None):
        data = {
            "compressNum": compress_num,
            "targets": {"actorId": [actor.actor_id for actor in actors]}
        }
        if path_tiles:
            data["pathTiles"] = path_tiles
        return self._send_request('query_tile', data)

    def find_path(self, actors, destination, method):
        data = {
            "targets": {"actorId": [actor.actor_id for actor in actors]},
            "destination": destination.to_dict(),
            "method": method
        }
        return self._send_request('find_path', data)
