import requests
import time
from pprint import pprint
from tqdm import tqdm
import numpy as np

LANGUAGES = [
    'JavaScript',
    'Java',
    'Python',
    'C#',
    'TypeScript',
    'PHP',
    'Kotlin',
    'C++'
]

API_METHOD_URL = "https://api.hh.ru/vacancies"
MAX_VACANCIES_QUANTITY = 2000
VACANCIES_PER_PAGE = 100


def predict_rub_salary(vacancy: dict):
    # TODO: оптимизировать код!
    salary_data = vacancy['salary']
    if salary_data['currency'] == 'RUR':
        if salary_data['from'] and salary_data['to']:
            salary = 0.5 * (salary_data['from'] + salary_data['to'])
        elif salary_data['from']:
            salary = 1.2 * salary_data['from']
        elif salary_data['to']:
            salary = 0.8 * salary_data['to']
        else:
            return None
        return salary
    return None


def main():
    vacancies_by_language = {key: {} for key in LANGUAGES}
    for language in tqdm(LANGUAGES):
        vacs = []
        found = 0
        processed = 0
        for page_number in range(int(MAX_VACANCIES_QUANTITY / VACANCIES_PER_PAGE)):
            params = {
                'text': f'Программист {language}',
                'area': 1,
                'period': 30,
                'page': page_number,
                'per_page': VACANCIES_PER_PAGE,
                'only_with_salary': True
            }
            response = requests.get(API_METHOD_URL, params)
            response.raise_for_status()
            vacancies = response.json()['items']
            # TODO: заменить на кол-во из респонса
            found += len(vacancies)
            # TODO: нужно добавить счётчик! (см. задание)
            salaries = []
            for vacancy in vacancies:
                salary = predict_rub_salary(vacancy)
                if salary:
                    salaries.append(salary)
                    processed += 1
            vacs.append(salaries)
            time.sleep(3)
        vacancies_by_language[language]['avg_salary'] = int(np.mean([x for y in vacs for x in y]))
        vacancies_by_language[language]['vacancies_found'] = found
        vacancies_by_language[language]['vacancies_processed'] = processed
        time.sleep(10)
    print(vacancies_by_language)


if __name__ == "__main__":
    main()


