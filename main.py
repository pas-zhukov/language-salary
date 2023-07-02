import os
import time

from dotenv import load_dotenv
import numpy as np
import requests
from tqdm import tqdm
from terminaltables import SingleTable

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


def main():
    load_dotenv()
    sj_secret_key = os.getenv('SJ_SECRET_KEY')
    statistics_headhunter = get_vacancies_statistics_hh()
    statistics_superjob = get_vacancies_statistics_sj(sj_secret_key)
    print_statistics_table('HeadHunter Moscow', statistics_headhunter)
    print_statistics_table('SuperJob Moscow', statistics_superjob)


def print_statistics_table(site_city_name: str, statistics: dict):
    """
    Prints table with vacancies statistics.

    Prints a table with statistics of vacancies found,
    processed, and average salary for each programming
    language in a given city and job search site.
    :param site_city_name: name of the job search site and city
    :param statistics: statistics of vacancies found
    :return: None
    """
    headers = ['Programming Language', 'Vacancies Found', 'Vacancies Processed', 'Average Salary']
    rows = [[language] + list(language_stats.values()) for language, language_stats in statistics.items()]
    table_title = site_city_name
    table_instance = SingleTable([headers] + rows, table_title)
    table_instance.justify_columns[1] = 'center'
    table_instance.justify_columns[2] = 'center'
    print(table_instance.table)
    print()


def predict_salary(salary_from, salary_to,
                   salary_from_coef: float = 1.2,
                   salary_to_coef: float = 0.8):
    """
    Predicts the average salary based on the given salary from/to values

    :param salary_from: lower salary bound
    :param salary_to: upper salary bound
    :param salary_from_coef: adjusting coefficient if 'salary_from' is the only available value
    :param salary_to_coef: adjusting coefficient if 'salary_to' is the only available value
    :return: predicted salary
    """
    if salary_from and salary_to:
        salary = (salary_from + salary_to) / 2  # mean
    elif salary_from:
        salary = salary_from_coef * salary_from
    elif salary_to:
        salary = salary_to_coef * salary_to
    else:
        return None
    return salary


def predict_rub_salary_hh(vacancy: dict):
    """
    Predicts salary based on the vacancy from HeadHunter site.

    :param vacancy: a dictionary containing information about a job vacancy
    :return: predicted salary
    """
    if vacancy['salary'] is None:
        return None
    salary = vacancy['salary']
    if salary['currency'] == 'RUR':
        return predict_salary(salary['from'],
                              salary['to'])
    return None


def predict_rub_salary_superjob(vacancy: dict):
    """
    Predicts salary based on the vacancy from SuperJob site.

    :param vacancy: a dictionary containing information about a job vacancy
    :return: predicted salary
    """
    if vacancy['currency'] == 'rub':
        return predict_salary(vacancy['payment_from'],
                              vacancy['payment_to'])
    return None


def get_vacancies_statistics_hh(period: int = 30):
    """
    Collects vacancies statistics from HeadHunter.

    Collects and computes statistics of vacancies found,
    processed, and average salary for each programming language
    in Moscow using the HeadHunter job search site.
    :param period: period in days to search for vacancies posted within
    :return: statistics of vacancies found, processed, and average salary for each programming language
    """
    vacancies_by_language = {key: {} for key in POPULAR_LANGUAGES}
    for language in tqdm(POPULAR_LANGUAGES):
        salaries = []
        vacancies_found = 0
        vacancies_processed = 0
        for page_number in range(int(SJ_MAX_VACANCIES_QUANTITY / SJ_VACANCIES_PER_PAGE)):
            params = {
                'text': f'Программист {language}',
                'area': HH_MOSCOW_ID,
                'period': period,
                'page': page_number,
                'per_page': HH_VACANCIES_PER_PAGE
            }
            response = requests.get(HH_API_METHOD_URL, params)
            response.raise_for_status()
            vacancies = response.json()['items']
            vacancies_found += len(vacancies)
            for vacancy in vacancies:
                salary = predict_rub_salary_hh(vacancy)
                if salary:
                    salaries.append(salary)
                    vacancies_processed += 1
            time.sleep(1)
        vacancies_by_language[language] = {
            'average_salary': int(np.mean(salaries)),
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed
        }
        time.sleep(5)
    return vacancies_by_language


def get_vacancies_statistics_sj(sj_secret_key: str, period: int = 30):
    """
    Collects vacancies statistics from SuperJob.

    Collects and computes statistics of vacancies found,
    processed, and average salary for each programming language
    in Moscow using the SuperJob job search site.
    :param sj_secret_key: secret key from your SJ API application page
    :param period: period in days to search for vacancies posted within
    :return: statistics of vacancies found, processed, and average salary for each programming language
    """
    vacancies_by_language = {key: {} for key in POPULAR_LANGUAGES}
    for language in tqdm(POPULAR_LANGUAGES):
        salaries = []
        vacancies_found = 0
        vacancies_processed = 0
        for page_number in range(int(SJ_MAX_VACANCIES_QUANTITY / SJ_VACANCIES_PER_PAGE)):
            auth_header = {"X-Api-App-Id": sj_secret_key}
            params = {
                'keyword': f'Программист {language}',
                'town': SJ_MOSCOW_ID,
                'period': period,
                'page': page_number,
                'count': SJ_VACANCIES_PER_PAGE,
            }
            response = requests.get(SJ_API_METHOD_URL, headers=auth_header, params=params)
            response.raise_for_status()
            vacancies = response.json()['objects']
            vacancies_found += len(vacancies)
            for vacancy in vacancies:
                salary = predict_rub_salary_superjob(vacancy)
                if salary:
                    salaries.append(salary)
                    vacancies_processed += 1
            time.sleep(1)
        vacancies_by_language[language] = {
            'average_salary': int(np.mean(salaries)),
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed
        }
        time.sleep(1)
    return vacancies_by_language


if __name__ == "__main__":
    main()
