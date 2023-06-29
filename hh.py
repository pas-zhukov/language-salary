import os
from dotenv import load_dotenv
import requests
import time
from pprint import pprint
from tqdm import tqdm
import numpy as np

POPULAR_LANGUAGES = [
    'JavaScript',
    'Java',
    'Python',
    'C#',
    'TypeScript',
    'PHP',
    'Kotlin',
    'C++'
]

HH_API_METHOD_URL = "https://api.hh.ru/vacancies"
HH_MAX_VACANCIES_QUANTITY = 2000
HH_VACANCIES_PER_PAGE = 100
HH_MOSCOW_ID = 1

SJ_API_METHOD_URL = "https://api.superjob.ru/2.0/vacancies/"
SJ_MAX_VACANCIES_QUANTITY = 500
SJ_VACANCIES_PER_PAGE = 100
SJ_MOSCOW_ID = 4


def predict_salary(salary_from, salary_to,
                   salary_from_coef: float = 1.2,
                   salary_to_coef: float = 0.8):
    if salary_from and salary_to:
        salary = (salary_from + salary_to) / 2  # mean
    elif salary_from:
        salary = salary_from_coef * salary_from
    elif salary_to:
        salary = salary_to_coef * salary_to
    else:
        print(None)
        return None
    print(salary)
    return salary


def predict_rub_salary_hh(vacancy: dict):
    salary = vacancy['salary']
    if salary['currency'] == 'RUR':
        return predict_salary(salary['from'],
                              salary['to'])
    return None


def predict_rub_salary_superjob(vacancy: dict):
    print(vacancy['payment_from'],
          vacancy['payment_to'], sep='-')
    if vacancy['currency'] == 'rub':
        return predict_salary(vacancy['payment_from'],
                              vacancy['payment_to'])
    return None

def get_vacancies_statistics(
        max_vacancies_quantity: int,
        vacancies_per_page: int,
        text_field_name: str,
        location_field_name: str,
        period_field_name: str = 'period',
        page_number_field_name: str = 'page',
        count_per_page_field_name: str = 'per_page',
        request_headers: dict = None,
        additional_request_params: dict = None,
        ) -> dict:
    pass


def get_vacancies_statistics_hh(period: int = 30):
    vacancies_by_language = {key: {} for key in POPULAR_LANGUAGES}
    for language in tqdm(POPULAR_LANGUAGES):
        total_salaries = []
        vacancies_found = 0
        vacancies_processed = 0
        for page_number in range(int(SJ_MAX_VACANCIES_QUANTITY / SJ_VACANCIES_PER_PAGE)):
            params = {
                'text': f'Программист {language}',
                'area': HH_MOSCOW_ID,
                'period': period,
                'page': page_number,
                'per_page': HH_VACANCIES_PER_PAGE,
                'only_with_salary': True
            }
            response = requests.get(HH_API_METHOD_URL, params)
            response.raise_for_status()
            vacancies = response.json()['items']
            vacancies_found += len(vacancies)
            salaries = []
            for vacancy in vacancies:
                salary = predict_rub_salary_hh(vacancy)
                if salary:
                    salaries.append(salary)
                    vacancies_processed += 1
            total_salaries.append(salaries)
            time.sleep(1)
        vacancies_by_language[language]['average_salary'] = int(np.mean([x for y in total_salaries for x in y]))
        vacancies_by_language[language]['vacancies_found'] = vacancies_found
        vacancies_by_language[language]['vacancies_processed'] = vacancies_processed
        time.sleep(5)
    return vacancies_by_language


def get_vacancies_statistics_sj(sj_secret_key: str, period: int = 30):
    vacancies_by_language = {key: {} for key in POPULAR_LANGUAGES}
    for language in tqdm(POPULAR_LANGUAGES):
        total_salaries = []
        vacancies_found = 0
        vacancies_processed = 0
        for page_number in range(int(SJ_MAX_VACANCIES_QUANTITY / SJ_VACANCIES_PER_PAGE)):
            headers = {"X-Api-App-Id": sj_secret_key}
            params = {
                'keyword': f'Программист {language}',
                'town': SJ_MOSCOW_ID,
                'period': period,
                'page': page_number,
                'count': SJ_VACANCIES_PER_PAGE,
            }
            response = requests.get(SJ_API_METHOD_URL, headers=headers, params=params)
            response.raise_for_status()
            vacancies = response.json()['objects']
            vacancies_found += len(vacancies)
            salaries = []
            for vacancy in vacancies:
                salary = predict_rub_salary_superjob(vacancy)
                if salary:
                    salaries.append(salary)
                    vacancies_processed += 1
            total_salaries.append(salaries)
            time.sleep(1)
        vacancies_by_language[language]['average_salary'] = int(np.mean([x for y in total_salaries for x in y]))
        vacancies_by_language[language]['vacancies_found'] = vacancies_found
        vacancies_by_language[language]['vacancies_processed'] = vacancies_processed
        time.sleep(1)
    return vacancies_by_language


def main():
    load_dotenv()
    sj_secret_key = os.getenv('SJ_SECRET_KEY')
    pprint(get_vacancies_statistics_sj(sj_secret_key))


if __name__ == "__main__":
    main()
