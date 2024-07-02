import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm
import robotexclusionrulesparser
from fake_useragent import UserAgent
import os
import aiofiles

url = 'https://mofa.gov.np/'
visited_urls = set()
ua = UserAgent()

async def save_visited_urls():
    async with aiofiles.open('visited_urls.txt', 'w') as file:
        for url in visited_urls:
            await file.write(url + '\n')

async def load_visited_urls():
    if os.path.exists('visited_urls.txt'):
        async with aiofiles.open('visited_urls.txt', 'r') as file:
            async for line in file:
                visited_urls.add(line.strip())

async def fetch_robots_txt(session, url):
    parsed_url = urlparse(url)
    robots_url = f'{parsed_url.scheme}://{parsed_url.netloc}/robots.txt'
    try:
        async with session.get(robots_url, timeout=10) as response:
            robots_txt = await response.text()
        rp = robotexclusionrulesparser.RobotExclusionRulesParser()
        rp.parse(robots_txt)
        return rp
    except Exception as e:
        print(f"Error fetching robots.txt: {e}")
        return None

def is_allowed(url, rp):
    return rp.is_allowed('*', url)

async def crawl_page(session, url, rp=None, semaphore=None):
    if url in visited_urls:
        return

    visited_urls.add(url)

    try:
        async with semaphore:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    print(f"Error fetching {url}: HTTP {response.status}")
                    return
                content = await response.text()
    except aiohttp.ClientError as e:
        print(f"Error fetching {url}: {e}")
        return
    except Exception as e:
        print(f"Unexpected error fetching {url}: {e}")
        return

    soup = BeautifulSoup(content, 'html.parser')

    tasks = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            absolute_url = urljoin(url, href)
            if absolute_url.startswith('https://mofa.gov.np/') and is_allowed(absolute_url, rp):
                print(f"Found link: {absolute_url}")
                tasks.append(crawl_page(session, absolute_url, rp, semaphore))

    await asyncio.gather(*tasks)

async def main():
    await load_visited_urls()

    async with aiohttp.ClientSession(headers={'User-Agent': ua.random}) as session:
        rp = await fetch_robots_txt(session, url)

        # Limit concurrent connections
        semaphore = asyncio.Semaphore(10)

        await crawl_page(session, url, rp, semaphore)

    await save_visited_urls()

if __name__ == "__main__":
    asyncio.run(main())