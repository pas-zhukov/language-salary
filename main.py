import requests

token = "v3.r.137457653.7ea316e15b259c72cbb425cd3ad5a3eef3eb21a2.fbe8484fa854ad9fd2cc55f3776bd60959941488"

header = {"X-Api-App-Id": token}
url = "https://api.superjob.ru/2.0/vacancies/"

params = {

}

response = requests.get(url, headers=header)
for obj in response.json()['objects']:
    print(obj['profession'])





