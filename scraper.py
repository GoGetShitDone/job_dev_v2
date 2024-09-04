import re
from typing import List, Iterator
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils import cached

# 웹 드라이버 설정
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_driver = webdriver.Chrome(options=chrome_options)


class JobDescription:
    def __init__(self, company_name: str, title: str, description: str, link: str, salary: str = "N/A", source: str = ""):
        self.company = company_name
        self.position = title
        self.description = description
        self.link = link
        self.salary = salary
        self.source = source
        self.skills = self.extract_skills(description)

    def extract_skills(self, description):
        skills = []
        common_skills = ["Python", "JavaScript", "React", "Node.js",
                         "SQL", "Java", "C++", "AWS", "Docker", "Kubernetes"]
        for skill in common_skills:
            if skill.lower() in description.lower():
                skills.append(skill)
        return skills


# Berlin Startup Jobs constants and helpers
BERLIN_BASE_URL = "https://berlinstartupjobs.com"
BERLIN_PARSER_NAME = 'html.parser'


def get_berlin_search_url(query: str, page: int) -> str:
    return f"{BERLIN_BASE_URL}/?s={query}&page={page}"


@cached
def scrap_berlin_job_descriptions(query: str) -> List[JobDescription]:
    results = []
    for jobs in _iter_scrap_berlin_job_descriptions(query):
        results.extend(jobs)
    return results


def _iter_scrap_berlin_job_descriptions(query: str) -> Iterator[List[JobDescription]]:
    page = 1
    while True:
        url = get_berlin_search_url(query=query, page=page)
        chrome_driver.get(url)
        try:
            WebDriverWait(chrome_driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ais-Hits"))
            )
        except TimeoutException:
            print(f"Timed out waiting for page (url: {url})")
            break

        soup = BeautifulSoup(chrome_driver.page_source,
                             features=BERLIN_PARSER_NAME)
        jobs = _get_berlin_job_descriptions(soup)

        if len(jobs) <= 0:
            break
        page += 1

        yield jobs


def _get_berlin_job_descriptions(soup: BeautifulSoup) -> List[JobDescription]:
    tags = soup.find_all(class_="bjs-jlid__wrapper")
    return [_map_berlin_job_description_from(tag) for tag in tags]


def _map_berlin_job_description_from(tag) -> JobDescription:
    title_header = tag.find(class_="bjs-jlid__h").findChild()
    return JobDescription(
        company_name=tag.find(class_="bjs-jlid__b").text,
        title=title_header.text,
        description=re.sub(r'\n', " | ", tag.find(
            class_="bjs-jlid__description").text.strip()),
        link=title_header.get('href'),
        source="Berlin Startup Jobs"
    )


# Web3 Jobs constants and helpers
WEB3_BASE_URL = "https://web3.career"
WEB3_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
WEB3_PARSER_NAME = 'html.parser'


def get_web3_tag_page_url(tag: str, page: int) -> str:
    return f"{WEB3_BASE_URL}/{tag}-jobs?page={page}"


def get_web3_job_detail_link(path: str) -> str:
    return f"{WEB3_BASE_URL}{path}"


@cached
def scrap_web3_job_descriptions(tag: str) -> List[JobDescription]:
    results = []
    for jobs in _iter_scrap_web3_job_descriptions(tag):
        results.extend(jobs)
    return results


def _iter_scrap_web3_job_descriptions(tag: str) -> Iterator[List[JobDescription]]:
    page = 1
    before_jobs = [JobDescription('', '', '', '')]
    while True:
        url = get_web3_tag_page_url(tag, page)
        response = requests.get(url=url, headers=WEB3_REQUEST_HEADERS)
        soup = BeautifulSoup(response.text, features=WEB3_PARSER_NAME)
        job_descriptions = _get_web3_job_descriptions(soup)

        if len(job_descriptions) <= 0 or before_jobs[-1].link == job_descriptions[-1].link:
            break
        page += 1
        before_jobs = job_descriptions

        yield job_descriptions


def _get_web3_job_descriptions(soup: BeautifulSoup) -> List[JobDescription]:
    tbody = soup.find(class_='tbody')
    if tbody is None:
        return []

    rows = tbody.find_all('tr')
    rows = [row for row in rows if set(row.get_attribute_list('class')) != {
        'border-paid-table', 'table_row'}]
    return [_map_web3_job_description_from(row) for row in rows]


def _map_web3_job_description_from(tag) -> JobDescription:
    job_title = tag.find(class_="job-title-mobile")
    job_locations = tag.find_all(class_="job-location-mobile")
    regions = [_tag.text for _tag in job_locations[1].find_all(
        'a')] if len(job_locations) > 1 else []
    tags = tag.find_all(class_="my-badge")
    salary_element = tag.find(class_='text-salary')
    salary = salary_element.text.strip() if salary_element else "N/A"

    return JobDescription(
        company_name=job_locations[0].find(
            'h3').text.strip() if job_locations else "N/A",
        title=job_title.find('h2').text.strip() if job_title else "N/A",
        description=f"regions: {', '.join(regions)} \n"
                    f"salary: {salary} \n"
                    f"badge: {', '.join([_tag.find('a').text.strip() for _tag in tags])}",
        link=get_web3_job_detail_link(job_title.find(
            'a').get('href')) if job_title else "#",
        salary=salary,
        source="Web3 Jobs"
    )
