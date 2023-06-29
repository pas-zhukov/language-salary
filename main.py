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


def get_vacancies_statistics(
        api_method_url: str,
        max_vacancies_quantity: int,
        vacancies_per_page: int,
        text_field_name: str,
        location_field_name: str,
        items_field_name: str,
        city_id: int,
        salary_prediction_function: callable,
        period_field_name: str = 'period',
        page_number_field_name: str = 'page',
        count_per_page_field_name: str = 'per_page',
        request_headers: dict = None,
        additional_request_params: dict = None,
        requests_delay: int = 5,
        period: int = 30
        ) -> dict:
    """
    Collects and computes vacancies statistics.

    The objective of the function is to retrieve statistics
    of vacancies found, processed, and average salary for
    each programming language in a given city and job search site
    :param api_method_url: URL of the API method to retrieve vacancies data
    :param max_vacancies_quantity: maximum number of vacancies to retrieve, based on API limitations
    :param vacancies_per_page: number of vacancies to retrieve per page, based on API limitations
    :param text_field_name: [API setting] name of the field to search for a specific keyword
    :param location_field_name: [API setting] name of the field to search for a specific location
    :param items_field_name: [API setting] name of the field containing the vacancies data
    :param city_id: ID of the city to search for vacancies
    :param salary_prediction_function: function to predict the salary of a vacancy, based on API you use
    :param period_field_name: [API setting] name of the field to search for vacancies posted within a specific period
    :param page_number_field_name: [API setting] name of the field to specify the page number of the vacancies data
    :param count_per_page_field_name: [API setting] name of the field to specify the number of vacancies per page
    :param request_headers: headers to include in the API request
    :param additional_request_params:  additional parameters to include in the API request
    :param requests_delay: delay in seconds between API requests
    :param period: period in days to search for vacancies posted within
    :return: statistics of vacancies found, processed, and average salary for each programming language
    """
    vacancies_by_language = {key: {} for key in POPULAR_LANGUAGES}
    for language in tqdm(POPULAR_LANGUAGES):
        total_salaries = []
        vacancies_found = 0
        vacancies_processed = 0
        for page_number in range(int(max_vacancies_quantity / vacancies_per_page)):
            headers = request_headers
            params = {
                text_field_name: f'Программист {language}',
                location_field_name: city_id,
                period_field_name: period,
                page_number_field_name: page_number,
                count_per_page_field_name: vacancies_per_page,
            }
            if additional_request_params:
                params.update(additional_request_params)
            response = requests.get(api_method_url, headers=headers, params=params)
            response.raise_for_status()
            vacancies = response.json()[items_field_name]
            vacancies_found += len(vacancies)
            salaries = []
            for vacancy in vacancies:
                salary = salary_prediction_function(vacancy)
                if salary:
                    salaries.append(salary)
                    vacancies_processed += 1
            total_salaries.append(salaries)
            time.sleep(1)
        vacancies_by_language[language]['vacancies_found'] = vacancies_found
        vacancies_by_language[language]['vacancies_processed'] = vacancies_processed
        vacancies_by_language[language]['average_salary'] = int(np.mean([x for y in total_salaries for x in y]))
        time.sleep(requests_delay)
    return vacancies_by_language


def get_vacancies_statistics_hh(period: int = 30):
    """
    Collects vacancies statistics from HeadHunter.

    Collects and computes statistics of vacancies found,
    processed, and average salary for each programming language
    in Moscow using the HeadHunter job search site.
    :param period: period in days to search for vacancies posted within
    :return: statistics of vacancies found, processed, and average salary for each programming language
    """
    additional_request_param = {'only_with_salary': True}

    statistics = get_vacancies_statistics(HH_API_METHOD_URL, HH_MAX_VACANCIES_QUANTITY, HH_VACANCIES_PER_PAGE,
                                          text_field_name='text',
                                          location_field_name='area',
                                          items_field_name='items',
                                          salary_prediction_function=predict_rub_salary_hh,
                                          city_id=HH_MOSCOW_ID,
                                          period=period,
                                          additional_request_params=additional_request_param,
                                          requests_delay=10)
    return statistics


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
    auth_header = {"X-Api-App-Id": sj_secret_key}

    statistics = get_vacancies_statistics(SJ_API_METHOD_URL, SJ_MAX_VACANCIES_QUANTITY, SJ_VACANCIES_PER_PAGE,
                                          text_field_name='keyword',
                                          location_field_name='town',
                                          items_field_name='objects',
                                          count_per_page_field_name='count',
                                          salary_prediction_function=predict_rub_salary_superjob,
                                          city_id=SJ_MOSCOW_ID,
                                          period=period,
                                          request_headers=auth_header,
                                          requests_delay=1)
    return statistics


if __name__ == "__main__":
    main()
