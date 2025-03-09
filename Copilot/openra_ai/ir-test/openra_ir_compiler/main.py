# openra_ir_compiler/main.py
from . import compile_ir

ir_example = {
    "version": "1.0",
    "actions": [
        {"id": "analyze_001", "type": "ANALYSIS", "command": "query_actor", "parameters": {"target": "units", "unit_types": ["基地"], "faction": "敌方"}},
        {"id": "produce_001", "type": "PRODUCE", "command": "produce_units", "parameters": {"unit_type": "坦克", "quantity": 4}},
        {"id": "group1_001", "type": "GROUP", "command": "form_group", "parameters": {"unit_type": "坦克", "quantity": 2, "group_id": 1}, "dependencies": ["produce_001"]},
        {"id": "move1_001", "type": "MOVE", "command": "move_units_by_path", "parameters": {"group_id": 1, "destination": {"type": "relative", "value": "敌方基地"}, "path_method": "左路"}, "dependencies": ["group1_001", "analyze_001"]}
    ],
    "metadata": {"timestamp": 1623456789.0, "command": "测试"}
}

if __name__ == "__main__":
    code = compile_ir(ir_example)
    print("<code>")
    print(code)
    print("</code>")
