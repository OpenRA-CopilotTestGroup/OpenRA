# openra_ir_compiler/generator.py
from .types import ActionType
from .exceptions import CodeGenerationError

class CodeGenerator:
    UNIT_TYPE_MAP = {
        "坦克": "TANK",
        "步兵": "INFANTRY",
        "基地": "BASE",
        "士兵": "INFANTRY",
        "步枪兵": "INFANTRY",
        "火箭兵": "ROCKET_INFANTRY",
        "电厂": "POWER_PLANT",
        "车间": "FACTORY",
        "雷达": "RADAR"
    }

    def __init__(self, actions):
        self.actions = actions
        self.code_lines = [
            "from game_api import EnhancedGameAPI, UnitType, ActionStatus",
            "api = EnhancedGameAPI('localhost')"
        ]
        self.variables = {}
        self.group_counter = 0

    def generate(self):
        for action in self.actions:
            handler = self._get_handler(action["type"])
            handler(action)
        return "\n".join(self.code_lines)

    def _get_handler(self, action_type):
        handlers = {
            ActionType.ANALYSIS: self._handle_analysis,
            ActionType.PRODUCE: self._handle_produce,
            ActionType.BUILD: self._handle_build,
            ActionType.GROUP: self._handle_group,
            ActionType.MOVE: self._handle_move,
            ActionType.ATTACK: self._handle_attack,
            ActionType.TACTIC: self._handle_tactic,
        }
        try:
            return handlers[ActionType(action_type)]
        except KeyError:
            raise CodeGenerationError(f"No handler for action type: {action_type}")

    def _handle_analysis(self, action):
        params = action["parameters"]
        var_name = f"{action['id'].replace('_', '')}_result"
        if action["command"] == "map_query":
            self.code_lines.append(f"{var_name} = api.map_query()")
            self.code_lines.append(f"if not {var_name}:")
            self.code_lines.append(f"    raise RuntimeError('No map data found')")
        elif action["command"] == "query_actor":
            unit_type = params.get("unit_types", [None])[0]
            faction = params.get("faction", "己方")
            restrain = params.get("restrain", [])
            for r in restrain:
                if r["key"] == "type" and r["value"]:
                    unit_type = r["value"]  # Override unit_type if restrain specifies it
            unit_type_eng = self.UNIT_TYPE_MAP.get(unit_type, unit_type.upper() if unit_type else "None")
            filters = f"unit_type=UnitType.{unit_type_eng} if '{unit_type}' else None, state='待命', faction='{faction}'"
            for r in restrain:
                if r["key"] == "visible" and r["value"]:
                    filters += ", area=None"
            self.code_lines.append(f"{var_name} = api.find_units({filters})")
            error_msg = f"No {unit_type or 'units'} found"
            self.code_lines.append(f"if not {var_name}:")
            self.code_lines.append(f"    raise RuntimeError('{error_msg}')")
        elif action["command"] == "player_base_info_query":
            self.code_lines.append(f"{var_name} = api.player_base_info_query()")
            self.code_lines.append(f"if not {var_name}:")
            self.code_lines.append(f"    raise RuntimeError('No player data found')")
        self.variables[action["id"]] = var_name

    def _handle_produce(self, action):
        params = action["parameters"]
        unit_type = params["unit_type"]
        unit_type_eng = self.UNIT_TYPE_MAP.get(unit_type, unit_type.upper())
        quantity = params["quantity"]
        self.code_lines.append(f"result = api.produce_unit(UnitType.{unit_type_eng}, quantity={quantity})")
        self.code_lines.append("if result.status != ActionStatus.SUCCESS and result.wait_id:")
        self.code_lines.append("    result = api.wait_for_action(result.wait_id)")
        self.code_lines.append("if result.status != ActionStatus.SUCCESS:")
        self.code_lines.append(f"    raise RuntimeError('Failed to produce {quantity} {unit_type}')")

    def _handle_build(self, action):
        params = action["parameters"]
        building = params["building"]
        building_eng = self.UNIT_TYPE_MAP.get(building, building.upper())
        self.code_lines.append(f"result = api.build_structure(UnitType.{building_eng})")
        self.code_lines.append("if result.status != ActionStatus.SUCCESS and result.wait_id:")
        self.code_lines.append("    result = api.wait_for_action(result.wait_id)")
        self.code_lines.append("if result.status != ActionStatus.SUCCESS:")
        self.code_lines.append(f"    raise RuntimeError('Failed to build {building}')")

    def _handle_group(self, action):
        params = action["parameters"]
        unit_type = params["unit_type"]
        unit_type_eng = self.UNIT_TYPE_MAP.get(unit_type, unit_type.upper())
        unit_var = "infantrys" if unit_type in ["步兵", "士兵", "步枪兵"] else f"{unit_type_eng.lower()}s"
        group_id = params.get("group_id")
        if group_id is None:
            self.group_counter += 1
            group_id = self.group_counter
            params["group_id"] = group_id  # Ensure it's set for downstream use
        var_name = f"group_{group_id}"
        if unit_type not in self.variables:
            self.code_lines.append(f"{unit_var} = api.find_units(unit_type=UnitType.{unit_type_eng}, state='待命')")
            self.variables[unit_type] = unit_var
        total_needed = sum(a["parameters"]["quantity"] for a in self.actions if a["type"] == "GROUP" and a["parameters"]["unit_type"] == params["unit_type"])
        self.code_lines.append(f"if len({unit_var}) < {total_needed}:")
        self.code_lines.append(f"    raise RuntimeError('Not enough {unit_type} for all groups (need {total_needed})')")
        start_idx = sum(a["parameters"]["quantity"] for a in self.actions if a["type"] == "GROUP" and a["parameters"]["unit_type"] == params["unit_type"] and a["parameters"].get("group_id", float('inf')) < group_id)
        end_idx = start_idx + params["quantity"]
        self.code_lines.append(f"{var_name} = {unit_var}[{start_idx}:{end_idx}]")
        self.variables[action["id"]] = var_name

    def _handle_move(self, action):
        params = action["parameters"]
        group_id = params.get("group_id")
        if group_id is not None:
            group_var = f"group_{group_id}"
            if group_var not in self.variables and action["id"] not in self.variables:
                # Fallback to dependency if group_id not directly defined
                group_var = self.variables.get(action["dependencies"][0], "actors")
            elif group_var not in self.variables:
                group_var = self.variables[action["id"]]
        else:
            group_var = self.variables.get(action["dependencies"][0], "actors")
        dest = params["destination"]["value"]
        if action["command"] == "move_units_by_path":
            method = params.get("path_method", "最短路")
            if dest in ["敌方基地", "ENEMY_BASE"]:
                enemy_var = self.variables.get(action["dependencies"][1 if group_id is not None else 0])
                self.code_lines.append(f"path = api.find_path({group_var}, {enemy_var}[0].position, '{method}')")
            else:
                self.code_lines.append(f"path = api.find_path({group_var}, 'map_center', '{method}')")
            self.code_lines.append(f"result = api.move_units_by_path({group_var}, path)")
        else:
            if dest in ["敌方基地", "ENEMY_BASE"]:
                enemy_var = self.variables.get(action["dependencies"][1 if group_id is not None else 0])
                self.code_lines.append(f"dest_pos = {enemy_var}[0].position")
                dest = "dest_pos"
            self.code_lines.append(f"result = api.move_units({{'actorId': [u.actor_id for u in {group_var}]}}, {dest})")
        self.code_lines.append("if result.status != ActionStatus.SUCCESS:")
        self.code_lines.append(f"    raise RuntimeError('Failed to move group to {dest}')")

    def _handle_attack(self, action):
        params = action["parameters"]
        group_id = params.get("group_id")
        if group_id is not None:
            group_var = f"group_{group_id}"
            if group_var not in self.variables:
                group_var = self.variables.get(action["dependencies"][0], "actors")
        else:
            group_var = self.variables.get(action["dependencies"][0], "actors")
        target = params["target"]
        target_type = target["type"]
        target_type_eng = self.UNIT_TYPE_MAP.get(target_type, target_type.upper())
        faction = target["faction"]
        self.code_lines.append(f"targets = api.find_units(unit_type=UnitType.{target_type_eng}, state='待命', faction='{faction}')")
        self.code_lines.append(f"if not targets:")
        self.code_lines.append(f"    raise RuntimeError('No {target_type} found')")
        self.code_lines.append(f"for unit in {group_var}:")
        self.code_lines.append(f"    result = api.move_units({{'actorId': [unit.actor_id]}}, targets[0].position)")
        self.code_lines.append(f"    if result.status != ActionStatus.SUCCESS:")
        self.code_lines.append(f"        print(f'Attack by {{unit.actor_id}} failed')")

    def _handle_tactic(self, action):
        params = action["parameters"]
        components = params["components"]
        target = params.get("target", {})
        strategy = params.get("strategy", "closest")
        condition = params.get("condition", "TARGETS_DESTROYED")
        interval = params.get("interval", 1.0)

        unit_type = components[0]["unit_type"]
        unit_type_eng = self.UNIT_TYPE_MAP.get(unit_type, unit_type.upper())
        group_var = self.variables.get(action["dependencies"][0], f"{unit_type_eng.lower()}s")
        self.code_lines.append(f"active_units = set({group_var})")
        self.code_lines.append(f"while active_units:")
        if target:
            target_type = target["type"]
            target_type_eng = self.UNIT_TYPE_MAP.get(target_type, target_type.upper())
            faction = target["faction"]
            filters = f"unit_type=UnitType.{target_type_eng}, state='待命', faction='{faction}'"
            for r in target.get("restrain", []):
                if r["key"] == "visible" and r["value"]:
                    filters += ", area=None"
            self.code_lines.append(f"    targets = api.find_units({filters})")
            self.code_lines.append(f"    if not targets:")
            self.code_lines.append(f"        print('All {target_type} destroyed, mission complete')")
            self.code_lines.append(f"        break")
        if strategy == "closest":
            self.code_lines.append(f"    def find_closest_target(unit, targets):")
            self.code_lines.append(f"        min_dist = float('inf')")
            self.code_lines.append(f"        closest = None")
            self.code_lines.append(f"        for t in targets:")
            self.code_lines.append(f"            dist = ((unit.position[0] - t.position[0])**2 + (unit.position[1] - t.position[1])**2)**0.5")
            self.code_lines.append(f"            if dist < min_dist:")
            self.code_lines.append(f"                min_dist = dist")
            self.code_lines.append(f"                closest = t")
            self.code_lines.append(f"        return closest")
            self.code_lines.append(f"    for unit in list(active_units):")
            self.code_lines.append(f"        target = find_closest_target(unit, targets)")
            self.code_lines.append(f"        if target:")
            self.code_lines.append(f"            print(f'Unit {{unit.actor_id}} attacking {{target.actor_id}} at {{target.position}}')")
            self.code_lines.append(f"            result = api.move_units({{'actorId': [unit.actor_id]}}, target.position)")
            self.code_lines.append(f"            if result.status != ActionStatus.SUCCESS:")
            self.code_lines.append(f"                print(f'Unit {{unit.actor_id}} failed to move')")
        self.code_lines.append(f"        unit_state = api.get_unit_by_id(unit.actor_id)")
        self.code_lines.append(f"        if not unit_state or not unit_state.is_alive:")
        self.code_lines.append(f"            print(f'Unit {{unit.actor_id}} destroyed, removing')")
        self.code_lines.append(f"            active_units.remove(unit)")
        self.code_lines.append(f"    import time")
        self.code_lines.append(f"    time.sleep({interval})")