# openra_ir_compiler/parser.py
from .types import ActionType, VALID_API_METHODS, ACTION_PARAM_SCHEMA
from .exceptions import IRValidationError

class IRParser:
    def __init__(self, ir_json):
        self.ir = ir_json
        self.parsed_actions = []

    def parse(self):
        """Validate and normalize the IR."""
        # Check top-level structure
        if "version" not in self.ir or "actions" not in self.ir:
            raise IRValidationError("IR must have 'version' and 'actions' fields")
        if self.ir["version"] != "1.0":
            raise IRValidationError(f"Unsupported IR version: {self.ir['version']}")

        # Parse each action
        for action in self.ir["actions"]:
            self._validate_action(action)
            self.parsed_actions.append(action)
        return self.parsed_actions

    def _validate_action(self, action):
        """Validate a single action."""
        required = ["id", "type", "command"]
        for field in required:
            if field not in action:
                raise IRValidationError(f"Action missing required field: {field}")

        # Validate action type
        try:
            action_type = ActionType(action["type"])
        except ValueError:
            raise IRValidationError(f"Invalid action type: {action['type']}")

        # Validate command
        if action["command"] not in VALID_API_METHODS:
            raise IRValidationError(f"Unknown API command: {action['command']}")

        # Validate parameters
        params = action.get("parameters", {})
        valid_params = ACTION_PARAM_SCHEMA[action_type]
        for param in params:
            if param not in valid_params:
                raise IRValidationError(f"Invalid parameter '{param}' for {action_type}")

        # Normalize defaults (e.g., quantity = 1)
        if action_type == ActionType.PRODUCE and "quantity" not in params:
            action["parameters"]["quantity"] = 1
