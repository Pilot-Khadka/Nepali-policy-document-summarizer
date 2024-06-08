import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from tqdm import tqdm
import robotexclusionrulesparser
from fake_useragent import UserAgent


url = 'https://mofa.gov.np/'
visited_urls = set()
ua = UserAgent()
def save_visited_urls():
    with open('visited_urls.txt', 'w') as file:
        for url in visited_urls:
            file.write(url + '\n')

def load_visited_urls():
    try:
        with open('visited_urls.txt', 'r') as file:
            for line in file:
                visited_urls.add(line.strip())
    except FileNotFoundError:
        pass

def fetch_robots_txt(session, url):
    parsed_url = urlparse(url)
    robots_url = f'{parsed_url.scheme}://{parsed_url.netloc}/robots.txt'
    response = session.get(robots_url)
    rp = robotexclusionrulesparser.RobotExclusionRulesParser()
    rp.parse(response.text)
    return rp

def is_allowed(url, rp):
    return rp.is_allowed('*', url)

def crawl_page(session, url, delay=1, rp=None):
    if url in visited_urls:
        return

    visited_urls.add(url)
    response = session.get(url)
    content = response.content
    soup = BeautifulSoup(content, 'html.parser')

    links = soup.find_all('a')
    for link in tqdm(links, desc=f'Crawling {url}'):
        href = link.get('href')
        if href:
            absolute_url = urljoin(url, href)
            if absolute_url.startswith('https://mofa.gov.np/') and is_allowed(absolute_url, rp):
                print(href)
                time.sleep(delay)
                crawl_page(session, absolute_url, delay, rp)

    save_visited_urls()

load_visited_urls()
with requests.Session() as session:
    session.headers.update({'User-Agent': ua.random})
    rp = fetch_robots_txt(session, url)
    crawl_page(session, url, rp=rp)
