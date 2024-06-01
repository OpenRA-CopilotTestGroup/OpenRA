import requests

url = 'http://localhost:8080/moveactor'
data = {
    'actorId': '245',  
    'direction': '2',          
    'distance': '3'            
}

response = requests.post(url, data=data)

print(f'Status Code: {response.status_code}')
print(f'Response: {response.text}')