# openra_ir_compiler/execute.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from openra_ir_compiler import compile_ir
from game_api import EnhancedGameAPI, UnitType, ActionStatus

def execute_generated_code(ir_json):
    # Compile IR to Python code
    code = compile_ir(ir_json)
    print("Generated Code:")
    print("<code>")
    print(code)
    print("</code>")

    # Execute the code
    print("\nExecuting Code...")
    try:
        # Create a local namespace with EnhancedGameAPI available
        namespace = {"EnhancedGameAPI": EnhancedGameAPI, "UnitType": UnitType, "ActionStatus": ActionStatus}
        exec(code, namespace)
        print("Execution completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")

if __name__ == "__main__":
    # Example IR for "两路夹击敌方基地"
    ir_example = {
        "version": "1.0",
        "actions": [
            {"id": "analyze_001", "type": "ANALYSIS", "command": "query_actor", "parameters": {"unit_types": ["基地"], "faction": "敌方"}},
            {"id": "produce_001", "type": "PRODUCE", "command": "produce_units", "parameters": {"unit_type": "坦克", "quantity": 4}, "dependencies": ["analyze_001"]},
            {"id": "group1_001", "type": "GROUP", "command": "form_group", "parameters": {"unit_type": "坦克", "quantity": 2, "group_id": 1}, "dependencies": ["produce_001"]},
            {"id": "group2_001", "type": "GROUP", "command": "form_group", "parameters": {"unit_type": "坦克", "quantity": 2, "group_id": 2}, "dependencies": ["produce_001"]},
            {"id": "move1_001", "type": "MOVE", "command": "move_units_by_path", "parameters": {"group_id": 1, "destination": {"type": "relative", "value": "敌方基地"}, "path_method": "左路"}, "dependencies": ["group1_001", "analyze_001"]},
            {"id": "move2_001", "type": "MOVE", "command": "move_units_by_path", "parameters": {"group_id": 2, "destination": {"type": "relative", "value": "敌方基地"}, "path_method": "右路"}, "dependencies": ["group2_001", "analyze_001"]}
        ],
        "metadata": {"timestamp": 1623456789.0, "command": "两路夹击敌方基地"}
    }
    execute_generated_code(ir_example)