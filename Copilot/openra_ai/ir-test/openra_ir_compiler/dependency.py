# openra_ir_compiler/dependency.py
from .exceptions import DependencyError

class DependencyResolver:
    def __init__(self, actions):
        self.actions = {action["id"]: action for action in actions}
        self.ordered = []

    def resolve(self):
        """Order actions based on dependencies."""
        visited = set()
        temp_mark = set()  # For cycle detection

        # Topological sort
        for action_id in self.actions:
            if action_id not in visited:
                self._visit(action_id, visited, temp_mark)

        return self.ordered  # No reversal here

    def _visit(self, action_id, visited, temp_mark):
        """DFS-based topological sort with cycle detection."""
        if action_id in temp_mark:
            raise DependencyError(f"Circular dependency detected at {action_id}")
        if action_id not in visited:
            temp_mark.add(action_id)
            action = self.actions.get(action_id)
            if not action:
                raise DependencyError(f"Dependency {action_id} not found")
            for dep_id in action.get("dependencies", []):
                self._visit(dep_id, visited, temp_mark)
            temp_mark.remove(action_id)
            visited.add(action_id)
            self.ordered.append(action)