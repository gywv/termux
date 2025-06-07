import asyncio
import aiohttp
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from typing import Set, List, Dict
import re

class AsyncCrawler:
    def __init__(self, start_url: str, domain: str, max_pages: int = 100, timeout: int = 3):
        self.start_url = start_url
        self.domain = domain
        self.max_pages = max_pages
        self.timeout = timeout
        
        self.visited_urls: Set[str] = set()
        self.results: List[Dict] = []
        self.total_pages = 0
        self.start_time = 0
        
    def normalize_url(self, url: str) -> str:
        """移除锚点,标准化URL"""
        return url.split('#')[0]
    
    def is_valid_url(self, url: str) -> bool:
        """检查URL是否合法且在目标域名下"""
        try:
            parsed = urlparse(url)
            return parsed.netloc == urlparse(self.domain).netloc
        except:
            return False
            
    async def fetch_page(self, session: aiohttp.ClientSession, url: str) -> Dict:
        """抓取单个页面"""
        try:
            async with session.get(url, timeout=self.timeout) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 提取标题
                    title = soup.title.string if soup.title else ''
                    
                    # 提取纯文本
                    texts = soup.stripped_strings
                    text_content = ' '.join(text for text in texts)
                    
                    # 提取链接
                    links = []
                    for a in soup.find_all('a', href=True):
                        link = urljoin(url, a['href'])
                        if self.is_valid_url(link):
                            links.append(self.normalize_url(link))
                    
                    return {
                        'url': url,
                        'title': title,
                        'text': text_content,
                        'links': links
                    }
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
        return None

    async def crawl(self):
        """主爬虫逻辑"""
        self.start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            # 初始化任务队列
            queue = asyncio.Queue()
            await queue.put(self.start_url)
            
            while not queue.empty() and self.total_pages < self.max_pages:
                # 获取当前队列中的所有URL
                current_urls = []
                try:
                    while not queue.empty() and len(current_urls) < self.max_pages - self.total_pages:
                        url = await queue.get()
                        if self.normalize_url(url) not in self.visited_urls:
                            current_urls.append(url)
                except asyncio.QueueEmpty:
                    pass
                
                if not current_urls:
                    break
                    
                # 并发抓取页面
                tasks = [self.fetch_page(session, url) for url in current_urls]
                results = await asyncio.gather(*tasks)
                
                # 处理结果
                for result in results:
                    if result:
                        self.visited_urls.add(self.normalize_url(result['url']))
                        self.results.append({
                            'url': result['url'],
                            'title': result['title'],
                            'text': result['text']
                        })
                        self.total_pages += 1
                        
                        # 将新链接加入队列
                        for link in result['links']:
                            if self.normalize_url(link) not in self.visited_urls:
                                await queue.put(link)
                                
        # 计算统计信息
        duration = time.time() - self.start_time
        pages_per_second = self.total_pages / duration
        print(f"\nCrawling completed:")
        print(f"Total pages: {self.total_pages}")
        print(f"Time taken: {duration:.2f} seconds")
        print(f"Speed: {pages_per_second:.2f} pages/second")
        
    def save_results(self, filename: str = 'crawler_results.json'):
        """保存结果到JSON文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

async def main():
    start_url = 'https://blog.bling.moe/tags/软路由/'
    domain = 'https://blog.bling.moe'
    crawler = AsyncCrawler(start_url, domain)
    await crawler.crawl()
    crawler.save_results()

if __name__ == '__main__':
    asyncio.run(main())