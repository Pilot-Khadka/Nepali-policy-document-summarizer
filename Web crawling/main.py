import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from tqdm import tqdm
import robotexclusionrulesparser
from fake_useragent import UserAgent
import os
import logging

ua = UserAgent()

def save_visited_urls(file_name, visited_urls):
    if not os.path.exists(file_name):
        open(file_name, 'w').close()
    with open(file_name, 'a') as file:
        for url in visited_urls:
            file.write(url + '\n')

def load_visited_urls(file_name):
    visited_urls = set()
    if not os.path.exists(file_name):
        open(file_name, 'w').close()
    else:
        with open(file_name, 'r') as file:
            for line in file:
                visited_urls.add(line.strip())
    return visited_urls

def is_valid_link(href):
    if href.startswith('#'):
        return False
    return True


def crawl_page(session, url, delay=0.01):
    logging.info(f"Start crawling {url}")
    visited_urls=load_visited_urls('visited_urls.txt')
    if url in visited_urls:
        logging.info(f"URL already visited: {url}")
        return

    save_visited_urls('visited_urls.txt',{url})
    try:
        response = session.get(url, timeout=10, verify=False) # Disable SSL verification
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        logging.error(f"Error fetching {url}: {e}")
        return
    content = response.content
    soup = BeautifulSoup(content, 'html.parser')

    links = soup.find_all('a')
    avoid_links = load_visited_urls('avoid.txt')
    new_urls = set()
    for link in tqdm(links, desc=f'Crawling {url}'):
        href = link.get('href')
        if not href:
            continue
        if any(avoid in href for avoid in avoid_links):
            print(f"Skipping {href} because it matches avoid list.")
            continue

        if is_valid_link(href):
            print("Valid link")
            if href.startswith('/'):
                href = requests.compat.urljoin(url, href)  # Handle relative URLs
            logging.info(f"Found link: {href}")
            new_urls.add(href)
            time.sleep(delay)
    print(new_urls)
    save_visited_urls('all_urls.txt', new_urls)
    logging.info(f"Finished crawling {url}")
    return new_urls

def main():
    logging.basicConfig(level=logging.INFO)
    if os.path.exists('all_urls.txt'):
        urls = load_visited_urls('all_urls.txt')
    else:
        urls = {'https://mofa.gov.np/'}
    iteration_count = 0
    while iteration_count < 100:
        if not urls:
            break
        url = urls.pop()
        with requests.Session() as session:
            session.headers.update({'User-Agent': ua.random})
            new_urls = crawl_page(session, url)
            if new_urls:
                urls.update(new_urls)
        iteration_count += 1
    save_visited_urls('all_urls.txt', urls)

if __name__=="__main__":
    main()
