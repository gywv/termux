import requests
import pickle
import os
import unittest
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import Set, List, Optional


DATA_FILE = 'crawler_state.data'

# -------------------------
# 📦 结构定义
# -------------------------
@dataclass
class CrawlResult:
    url: str
    title: str

@dataclass
class CrawlerState:
    to_visit: Set[str] = field(default_factory=set)
    visited: Set[str] = field(default_factory=set)
    results: List[CrawlResult] = field(default_factory=list)


# -------------------------
# 🕷️ 爬虫类
# -------------------------
class SimpleCrawler:
    def __init__(self, start_urls):
        self.state = CrawlerState(set(start_urls))
        self.load_state()

    def fetch(self, url: str) -> Optional[str]:
        try:
            print(f"Crawling: {url}")
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def parse(self, html: str, url: str) -> (CrawlResult, Set[str]):
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string.strip() if soup.title else 'No Title'
        return CrawlResult(url=url, title=title), set()

    def crawl(self, max_pages=100):
        while self.state.to_visit and len(self.state.visited) < max_pages:
            url = self.state.to_visit.pop()
            if url in self.state.visited:
                continue

            html = self.fetch(url)
            if html:
                result, new_links = self.parse(html, url)
                self.state.results.append(result)
                self.state.visited.add(url)
                self.state.to_visit.update(new_links - self.state.visited)

            self.save_state()


    def save_state(self):
        with open(DATA_FILE, 'wb') as f:
            pickle.dump(self.state, f)
        print(f"✅ State saved. Visited: {len(self.state.visited)}")

    def load_state(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'rb') as f:
                self.state = pickle.load(f)
            print(f"🔄 State loaded. Resuming from visited: {len(self.state.visited)}")
        else:
            print("🆕 No previous state found. Starting fresh.")


# -------------------------
# 🔍 查询接口类
# -------------------------
class ResultQuery:
    def __init__(self, data_file=DATA_FILE):
        self.state: CrawlerState = self.load_state(data_file)

    def load_state(self, file_path: str) -> CrawlerState:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        else:
            raise FileNotFoundError(f"Data file {file_path} not found.")

    def search_by_title_keyword(self, keyword: str) -> List[CrawlResult]:
        return [item for item in self.state.results if keyword.lower() in item.title.lower()]

    def search_by_url(self, url: str) -> Optional[CrawlResult]:
        for item in self.state.results:
            if item.url == url:
                return item
        return None

    def all_results(self) -> List[CrawlResult]:
        return self.state.results


# -------------------------
# ✅ 测试类
# -------------------------
class TestCrawlerAndQuery(unittest.TestCase):
    def test_crawling_and_query(self):
        # Step 1: Run the crawler
        seed_urls = ['https://example.com']
        crawler = SimpleCrawler(seed_urls)
        crawler.crawl(max_pages=1)  # 限制页面数便于测试

        # Step 2: Query results
        query = ResultQuery()

        print("\n🔍 Results with keyword 'Example':")
        results = query.search_by_title_keyword('Example')
        for result in results:
            print(result)
        self.assertTrue(any('Example' in r.title for r in results))

        print("\n🔗 Search by URL:")
        result = query.search_by_url('https://example.com')
        print(result)
        self.assertIsNotNone(result)
        self.assertEqual(result.url, 'https://example.com')


# -------------------------
# 🏁 启动测试
# -------------------------
if __name__ == "__main__":
    unittest.main()
