"""
Modular News Source System for SRCC
Easy to add/remove feeds, consistent data structure, versioned schemas
"""
import requests
import re
import os
import json
from datetime import datetime
from abc import ABC, abstractmethod

class NewsSource(ABC):
    """Base class for news sources"""
    
    def __init__(self, name, url, category='general', enabled=True):
        self.name = name
        self.url = url
        self.category = category
        self.enabled = enabled
    
    @abstractmethod
    def fetch(self, max_items=10):
        """Fetch articles from this source"""
        pass
    
    def estimate_read_time(self, title):
        """Estimate read time based on title length (rough heuristic)"""
        words = len(title.split())
        minutes = max(1, words // 200)  # ~200 words per minute
        return minutes
    
    def get_source_badge(self):
        """Get a short badge for the source"""
        return self.name[:12]


class RSSSource(NewsSource):
    """RSS/Atom feed source"""
    
    def fetch(self, max_items=10):
        try:
            resp = requests.get(self.url, timeout=8)
            content = resp.text
            
            articles = []
            
            # Try RSS <item> first, then Atom <entry>
            items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
            if not items:
                items = re.findall(r'<entry>(.*?)</entry>', content, re.DOTALL)
            
            for item in items[:max_items]:
                # Title: handle both RSS and Atom
                title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>', item)
                title = (title_match.group(1) or title_match.group(2) or "No title").strip() if title_match else "No title"
                
                # Link: handle both RSS and Atom
                link_match = re.search(r'<link>(.*?)</link>|<link href="([^"]+)"', item)
                link = (link_match.group(1) or link_match.group(2) or "#").strip() if link_match else "#"
                
                # Published date
                pub_match = re.search(r'<pubDate>(.*?)</pubDate>|<published>(.*?)</published>', item)
                pub_date = (pub_match.group(1) or pub_match.group(2) or "").strip() if pub_match else ""
                
                # Description/summary
                desc_match = re.search(r'<description><!\[CDATA\[(.*?)\]\]></description>|<description>(.*?)</description>', item)
                summary = (desc_match.group(1) or desc_match.group(2) or "")[:200].strip() if desc_match else ""
                
                if title and title != "No title" and link != "#":
                    articles.append({
                        'title': title[:100],
                        'link': link,
                        'source': self.get_source_badge(),
                        'category': self.category,
                        'published': pub_date,
                        'summary': summary,
                        'read_time_min': self.estimate_read_time(title)
                    })
            
            return articles
        except Exception as e:
            print(f"Error fetching {self.name}: {e}")
            return []


class HackerNewsSource(NewsSource):
    """Hacker News API source"""
    
    def fetch(self, max_items=10):
        try:
            # Use HN Firebase API
            resp = requests.get(f"https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10)
            story_ids = resp.json()[:max_items]
            
            articles = []
            for story_id in story_ids:
                story_resp = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json", timeout=5)
                story = story_resp.json()
                
                if story and story.get('title'):
                    articles.append({
                        'title': story.get('title', '')[:100],
                        'link': story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                        'source': 'Hacker News',
                        'category': 'tech',
                        'published': '',
                        'summary': f"{story.get('score', 0)} points · {story.get('descendants', 0)} comments",
                        'read_time_min': self.estimate_read_time(story.get('title', ''))
                    })
            
            return articles
        except Exception as e:
            print(f"Error fetching HN: {e}")
            return []


class APISource(NewsSource):
    """Generic API source (for future use)"""
    
    def __init__(self, name, url, category='general', enabled=True, headers=None):
        super().__init__(name, url, category, enabled)
        self.headers = headers or {}
    
    def fetch(self, max_items=10):
        try:
            resp = requests.get(self.url, headers=self.headers, timeout=10)
            data = resp.json()
            
            # Override in subclass for specific API formats
            articles = []
            for item in data[:max_items]:
                articles.append({
                    'title': item.get('title', '')[:100],
                    'link': item.get('url', item.get('link', '#')),
                    'source': self.get_source_badge(),
                    'category': self.category,
                    'published': item.get('published', ''),
                    'summary': item.get('description', '')[:200],
                    'read_time_min': self.estimate_read_time(item.get('title', ''))
                })
            return articles
        except Exception as e:
            print(f"Error fetching {self.name}: {e}")
            return []


# Source registry - add new sources here
def get_all_sources():
    """Get all configured news sources"""
    return [
        # Tech sources
        RSSSource('TechCrunch', 'https://techcrunch.com/feed/', 'tech'),
        RSSSource('The Verge', 'https://www.theverge.com/rss/index.xml', 'tech'),
        RSSSource('Wired', 'https://www.wired.com/feed/rss', 'tech'),
        RSSSource('Ars Technica', 'https://feeds.arstechnica.com/arstechnica/index', 'tech'),
        HackerNewsSource('Hacker News', 'https://hacker-news.firebaseio.com/v0/topstories.json', 'tech'),
        
        # World news
        RSSSource('BBC World', 'https://feeds.bbci.co.uk/news/world/rss.xml', 'world'),
        RSSSource('NYT World', 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml', 'world'),
        RSSSource('Reuters', 'https://www.reutersagency.com/feed/?best-topics=tech', 'world'),
        
        # Sports
        RSSSource('ESPN', 'https://www.espn.com/espn/rss/news', 'sports'),
        RSSSource('Yahoo Sports', 'https://sports.yahoo.com/rss/', 'sports'),
        
        # Soccer
        RSSSource('Goal.com', 'https://www.goal.com/en-us/feeds/rss/news', 'soccer'),
        RSSSource('ESPN Soccer', 'https://www.espn.com/soccer/rss/_/league/all', 'soccer'),
    ]


def get_sources_by_category():
    """Get sources grouped by category"""
    sources = get_all_sources()
    by_category = {}
    for source in sources:
        if source.enabled:
            if source.category not in by_category:
                by_category[source.category] = []
            by_category[source.category].append(source)
    return by_category


def fetch_all_articles(max_per_source=5):
    """Fetch articles from all enabled sources"""
    sources = get_all_sources()
    all_articles = []
    seen_titles = set()
    
    for source in sources:
        if source.enabled:
            articles = source.fetch(max_per_source)
            for article in articles:
                # Dedupe by title
                if article['title'] not in seen_titles:
                    all_articles.append(article)
                    seen_titles.add(article['title'])
    
    return all_articles


# Cache management
CACHE_FILE = os.path.join(os.path.dirname(__file__), 'data', 'sources_cache.json')

def get_cached_articles(max_per_source=5, max_total=30):
    """Get articles with caching (for daily digest)"""
    cache_age = None
    
    # Check cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cached = json.load(f)
            
            cached_time = datetime.fromisoformat(cached.get('cached_at', '2000-01-01'))
            cache_age = (datetime.now() - cached_time).total_seconds()
            
            # Return cached if less than 1 hour old
            if cache_age < 3600:
                articles = cached.get('articles', [])
                # Limit total
                return articles[:max_total]
        except:
            pass
    
    # Fetch fresh
    articles = fetch_all_articles(max_per_source)
    
    # Cache it
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump({
            'cached_at': datetime.now().isoformat(),
            'articles': articles
        }, f)
    
    return articles[:max_total]


def clear_cache():
    """Clear the sources cache"""
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
    return True
