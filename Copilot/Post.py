import requests
import json

url = 'http://localhost:8080' 
headers = {'Content-Type': 'application/json'}

data = {
    'command': 'selectunit',
    'targets':{
    'range': 'screen', #约束选择的目标基础 还可以为selected/all 没有此项默认为all 
    'groupId' : [2],  #约束目标的groupId，是个list，为空或者没有此项默认为不约束groupId
    'type': ['e1', 'e2'] #约束
    },
    'units': [
        'apwr',
        'proc','proc','proc',
        'silo',
        'ltnk',
        'tank'
        
    ],
    #'actorId': 246,
    'groupId': 2, 
     'location': {
        "X": '74',
        "Y": '81'
    },   
    'distance': 20 ,
    'direction': 3 ,
    'attackmove': True ,
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