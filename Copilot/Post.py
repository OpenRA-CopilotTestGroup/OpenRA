import requests
import json

url = 'http://localhost:8080' 
headers = {'Content-Type': 'application/json'}

data = {
    'command': 'moveactor',
    'groupId': '1', 
    'location': {
        "X": '74',
        "Y": '81'
    },
    'direction': 7,          
    'distance': 2            
}
json_data = json.dumps(data)

try:
    response = requests.post(url, headers=headers, data=json_data)

    if 'application/json' in response.headers.get('Content-Type', ''):
        response_data = response.json()
        print("Response JSON:")
        print(json.dumps(response_data, indent=4))
    else:
        print("Response is not in JSON format")
        print("Response Text:")
        print(response.text)
except requests.exceptions.RequestException as e:
    print(f'Request failed: {e}')