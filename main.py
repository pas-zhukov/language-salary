import requests


def predict_rub_salary_for_superjob(vacancy: dict):
    if vacancy['currency'] == 'rub':
        if vacancy['payment_from'] and vacancy['payment_to']:
            salary = 0.5 * (vacancy['payment_from'] + vacancy['payment_to'])
        elif vacancy['payment_from']:
            salary = 1.2 * vacancy['payment_from']
        elif vacancy['payment_to']:
            salary = 0.8 * vacancy['payment_to']
        else:
            return None
        return salary
    return None


token = "v3.r.137457653.7ea316e15b259c72cbb425cd3ad5a3eef3eb21a2.fbe8484fa854ad9fd2cc55f3776bd60959941488"

header = {"X-Api-App-Id": token}
url = "https://api.superjob.ru/2.0/vacancies/"

params = {
    'keyword': 'программист C++',
    'town': 4,
    'period': 30,
    'page':1 ,
    'count': 100
}

response = requests.get(url, headers=header, params=params)
for obj in response.json()['objects']:
    print(obj['profession'], obj['town']['title'], sep=', ')





