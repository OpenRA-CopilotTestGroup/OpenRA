# openra_ir_compiler/types.py
from enum import Enum

class ActionType(Enum):
    ANALYSIS = "ANALYSIS"
    PRODUCE = "PRODUCE"
    BUILD = "BUILD"
    GROUP = "GROUP"
    MOVE = "MOVE"
    ATTACK = "ATTACK"
    TACTIC = "TACTIC"

# Known GameAPI methods
VALID_API_METHODS = {
    "map_query": [],
    "query_actor": ["query_params"],
    "player_base_info_query": [],
    "produce_units": ["unit_type", "quantity"],
    "ensure_can_produce_unit": ["unit_type"],
    "form_group": ["actors", "group_id"],
    "move_units_by_path": ["actors", "path"],
    "find_path": ["actors", "destination", "method"],
    "attack_target": ["attacker", "target"],
    "move_units_by_location": ["actors", "location"]
}

# Valid parameter fields per action type (for validation)
ACTION_PARAM_SCHEMA = {
    ActionType.ANALYSIS: {"target", "unit_types", "faction", "range", "scan_for", "restrain"},  # Add "restrain"
    ActionType.PRODUCE: ["unit_type", "quantity", "rally_point"],
    ActionType.BUILD: ["building", "location"],
    ActionType.GROUP: ["unit_type", "quantity", "group_id", "formation"],
    ActionType.MOVE: ["unit_type", "group_id", "destination", "path_method", "attack_move"],
    ActionType.ATTACK: ["unit_type", "group_id", "target", "engagement"],
    ActionType.TACTIC: ["components", "engagement"]
}
