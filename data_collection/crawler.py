"""
(G)I-DLE Universe 数据采集模块
支持多网站爬取、数据清理和翻译
"""
import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin, urlparse
import argparse

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import config

@dataclass
class CrawlResult:
    """爬取结果数据类"""
    url: str
    title: str
    content: str
    timestamp: datetime
    source: str
    language: str = "en"
    translated: bool = False

class BaseCrawler:
    """基础爬虫类"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.logger = logging.getLogger(__name__)
    
    def crawl(self, url: str) -> Optional[CrawlResult]:
        """爬取单个页面"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return self.parse_content(response.text, url)
        except Exception as e:
            self.logger.error(f"爬取失败 {url}: {e}")
            return None
    
    def parse_content(self, html: str, url: str) -> Optional[CrawlResult]:
        """解析页面内容 - 子类需要重写"""
        raise NotImplementedError

class WikipediaCrawler(BaseCrawler):
    """Wikipedia 爬虫"""
    
    def parse_content(self, html: str, url: str) -> Optional[CrawlResult]:
        soup = BeautifulSoup(html, 'html.parser')
        
        # 获取标题
        title_elem = soup.find('h1', {'id': 'firstHeading'})
        title = title_elem.get_text().strip() if title_elem else "Unknown"
        
        # 获取主要内容
        content_div = soup.find('div', {'id': 'mw-content-text'})
        if not content_div:
            return None
        
        # 提取文本内容
        paragraphs = content_div.find_all(['p', 'h2', 'h3', 'h4'])
        content_parts = []
        
        for p in paragraphs:
            text = p.get_text().strip()
            if text and len(text) > 50:  # 过滤太短的段落
                content_parts.append(text)
        
        content = '\n\n'.join(content_parts)
        
        return CrawlResult(
            url=url,
            title=title,
            content=content,
            timestamp=datetime.now(),
            source="wikipedia"
        )

class NewsCrawler(BaseCrawler):
    """新闻网站爬虫"""
    
    def parse_content(self, html: str, url: str) -> Optional[CrawlResult]:
        soup = BeautifulSoup(html, 'html.parser')
        
        # 获取标题
        title_elem = soup.find('title')
        title = title_elem.get_text().strip() if title_elem else "Unknown"
        
        # 获取主要内容 (根据网站结构调整)
        content_selectors = [
            'article',
            '.post-content',
            '.entry-content',
            '.article-content',
            'main'
        ]
        
        content = ""
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                paragraphs = content_elem.find_all('p')
                content_parts = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
                content = '\n\n'.join(content_parts)
                break
        
        if not content:
            # 备用方案：获取所有段落
            paragraphs = soup.find_all('p')
            content_parts = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
            content = '\n\n'.join(content_parts)
        
        return CrawlResult(
            url=url,
            title=title,
            content=content,
            timestamp=datetime.now(),
            source="news"
        )

class RedditCrawler(BaseCrawler):
    """Reddit 爬虫"""
    
    def parse_content(self, html: str, url: str) -> Optional[CrawlResult]:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Reddit 内容通常在特定的 div 中
        posts = soup.find_all('div', {'data-testid': 'post-container'})
        
        content_parts = []
        for post in posts[:10]:  # 限制帖子数量
            title_elem = post.find('h3')
            content_elem = post.find('div', {'data-testid': 'post-content'})
            
            if title_elem:
                title = title_elem.get_text().strip()
                content_parts.append(f"标题: {title}")
            
            if content_elem:
                content = content_elem.get_text().strip()
                if content:
                    content_parts.append(f"内容: {content}")
        
        return CrawlResult(
            url=url,
            title="Reddit (G)I-DLE 讨论",
            content='\n\n'.join(content_parts),
            timestamp=datetime.now(),
            source="reddit"
        )

class DataCollector:
    """数据采集管理器"""
    
    def __init__(self):
        self.config = config.crawler
        self.logger = logging.getLogger(__name__)
        self.crawlers = {
            'wikipedia': WikipediaCrawler(self.config.websites['wikipedia']),
            'news': NewsCrawler(self.config.websites['soompi']),
            'reddit': RedditCrawler(self.config.websites['reddit'])
        }
        
        # 确保目录存在
        os.makedirs(self.config.raw_data_dir, exist_ok=True)
        os.makedirs(self.config.processed_data_dir, exist_ok=True)
    
    def crawl_site(self, site_name: str) -> List[CrawlResult]:
        """爬取单个网站"""
        if site_name not in self.config.websites:
            self.logger.error(f"未知网站: {site_name}")
            return []
        
        site_config = self.config.websites[site_name]
        if not site_config['enabled']:
            self.logger.info(f"网站 {site_name} 已禁用")
            return []
        
        self.logger.info(f"开始爬取网站: {site_name}")
        
        # 根据网站类型选择爬虫
        if site_config['type'] == 'wikipedia':
            crawler = self.crawlers['wikipedia']
        elif site_config['type'] == 'news':
            crawler = self.crawlers['news']
        elif site_config['type'] == 'community':
            crawler = self.crawlers['reddit']
        else:
            self.logger.error(f"不支持的网站类型: {site_config['type']}")
            return []
        
        # 爬取数据
        result = crawler.crawl(site_config['url'])
        if result:
            return [result]
        return []
    
    def crawl_all_sites(self) -> List[CrawlResult]:
        """爬取所有启用的网站"""
        all_results = []
        
        for site_name, site_config in self.config.websites.items():
            if site_config['enabled']:
                results = self.crawl_site(site_name)
                all_results.extend(results)
                
                # 添加延迟避免被封
                time.sleep(self.config.delay_between_requests)
        
        return all_results
    
    def save_results(self, results: List[CrawlResult], filename: str = None):
        """保存爬取结果"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crawl_results_{timestamp}.json"
        
        filepath = os.path.join(self.config.raw_data_dir, filename)
        
        # 转换为可序列化的格式
        serializable_results = []
        for result in results:
            serializable_results.append({
                'url': result.url,
                'title': result.title,
                'content': result.content,
                'timestamp': result.timestamp.isoformat(),
                'source': result.source,
                'language': result.language,
                'translated': result.translated
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"保存了 {len(results)} 条结果到 {filepath}")
        return filepath
    
    def load_results(self, filepath: str) -> List[CrawlResult]:
        """加载爬取结果"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        results = []
        for item in data:
            result = CrawlResult(
                url=item['url'],
                title=item['title'],
                content=item['content'],
                timestamp=datetime.fromisoformat(item['timestamp']),
                source=item['source'],
                language=item['language'],
                translated=item['translated']
            )
            results.append(result)
        
        return results

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='爬取 (G)I-DLE 相关信息')
    parser.add_argument('--site', type=str, help='指定爬取的网站')
    parser.add_argument('--all', action='store_true', help='爬取所有网站')
    parser.add_argument('--start-year', type=int, default=2018, help='开始年份')
    parser.add_argument('--end-year', type=int, default=2024, help='结束年份')
    parser.add_argument('--max-memory', type=str, default='2GB', help='最大内存限制')
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建数据采集器
    collector = DataCollector()
    
    # 更新配置
    collector.config.start_year = args.start_year
    collector.config.end_year = args.end_year
    collector.config.max_memory = args.max_memory
    
    if args.site:
        # 爬取指定网站
        results = collector.crawl_site(args.site)
    elif args.all:
        # 爬取所有网站
        results = collector.crawl_all_sites()
    else:
        print("请指定 --site 或 --all 参数")
        return
    
    if results:
        # 保存结果
        filepath = collector.save_results(results)
        print(f"爬取完成，共获取 {len(results)} 条数据")
        print(f"数据保存到: {filepath}")
    else:
        print("未获取到任何数据")

if __name__ == "__main__":
    main() 