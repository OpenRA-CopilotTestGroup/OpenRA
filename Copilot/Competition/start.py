import socket
import json
import uuid

payload = {
    "apiVersion": "1.0",
    "requestId": str(uuid.uuid4()),
    "command": "deploy",
    "params": {
        "targets": {
            "type": ["基地车"],
            "faction": "己方"
        }
    },
    "language": "zh"
}

data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(("127.0.0.1", 7445))
    s.sendall(data)
