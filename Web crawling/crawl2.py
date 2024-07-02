import requests
from bs4 import BeautifulSoup
import urllib.robotparser as robotparser
from urllib.parse import urljoin
from tqdm import tqdm
import time
from fake_useragent import UserAgent
import os

url = 'https://mofa.gov.np/'
visited_urls = set()
ua = UserAgent()

def save_visited_urls():
    with open('visited_urls.txt', 'w') as file:
        for url in visited_urls:
            file.write(url + '\n')

def load_visited_urls():
    if os.path.exists('visited_urls.txt'):
        with open('visited_urls.txt', 'r') as file:
            for line in file:
                visited_urls.add(line.strip())

def is_allowed(url, rp):
    return rp.is_allowed('*', url)

def extract_and_save_links(session, url, rp=None):
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('a')

    with open('links.txt', 'a') as file:
        for link in links:
            href = link.get('href')
            if href:
                absolute_url = urljoin(url, href)
                if absolute_url.startswith('https://mofa.gov.np/') and is_allowed(absolute_url, rp):
                    file.write(absolute_url + '\n')

def crawl_page(session, url, delay=0.01, rp=None):
    with open('links.txt', 'r') as file:
        all_links = set(file.read().splitlines())

    if url not in all_links:
        return

    if url in visited_urls:
        return

    visited_urls.add(url)

    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('a')

    for link in tqdm(links, desc=f'Crawling {url}'):
        href = link.get('href')
        if href:
            absolute_url = urljoin(url, href)
            if absolute_url.startswith('https://mofa.gov.np/') and is_allowed(absolute_url, rp):
                time.sleep(delay)
                crawl_page(session, absolute_url, delay, rp)

    save_visited_urls()

def main():
    session = requests.Session()
    rp = robotparser.RobotFileParser()
    rp.set_url("https://mofa.gov.np/robots.txt")
    rp.read()

    start_url = "https://mofa.gov.np/"

    # First, extract and save all links
    extract_and_save_links(session, start_url, rp)

    # Then, crawl the pages
    crawl_page(session, start_url, rp=rp)

if __name__ == "__main__":
    main()