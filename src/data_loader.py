"""
Data Loader - Fetch and process financial news articles
Run this once to populate data/articles.json
"""
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import re
import os

from src.config import NEWS_API_KEY, NEWS_QUERIES


def fetch_news_articles(
    queries: List[str] = NEWS_QUERIES,
    days_back: int = 7,
    max_articles_per_query: int = 20
) -> List[Dict]:
    """
    Fetch financial news articles from NewsAPI
    
    Args:
        queries: List of search terms
        days_back: How many days back to search
        max_articles_per_query: Max articles per search query
    
    Returns:
        List of article dictionaries
    """
    if not NEWS_API_KEY:
        raise ValueError("NEWS_API_KEY not found in environment variables")
    
    base_url = "https://newsapi.org/v2/everything"
    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    all_articles = []
    seen_urls = set()
    
    for query in queries:
        params = {
            "q": query,
            "from": from_date,
            "sortBy": "relevancy",
            "language": "en",
            "pageSize": max_articles_per_query,
            "apiKey": NEWS_API_KEY
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "ok":
                for article in data.get("articles", []):
                    # Skip duplicates
                    if article.get("url") in seen_urls:
                        continue
                    seen_urls.add(article.get("url"))
                    
                    # Skip articles with no content
                    if not article.get("content") and not article.get("description"):
                        continue
                    
                    all_articles.append({
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "content": article.get("content", ""),
                        "url": article.get("url", ""),
                        "source": article.get("source", {}).get("name", "Unknown"),
                        "published_at": article.get("publishedAt", ""),
                        "query": query
                    })
                    
            print(f"Fetched {len(data.get('articles', []))} articles for '{query}'")
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching articles for '{query}': {e}")
            continue
    
    print(f"\nTotal unique articles fetched: {len(all_articles)}")
    return all_articles


def clean_text(text: str) -> str:
    """Clean article text by removing HTML tags and extra whitespace"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove [+chars] patterns (NewsAPI truncation markers)
    text = re.sub(r'\[\+\d+ chars\]', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def process_articles(articles: List[Dict]) -> List[Dict]:
    """
    Process and clean articles for storage
    
    Args:
        articles: Raw articles from NewsAPI
    
    Returns:
        Cleaned and processed articles
    """
    processed = []
    
    for article in articles:
        # Combine content sources
        full_content = " ".join(filter(None, [
            article.get("title", ""),
            article.get("description", ""),
            article.get("content", "")
        ]))
        
        cleaned_content = clean_text(full_content)
        
        if len(cleaned_content) < 100:  # Skip very short articles
            continue
        
        processed.append({
            "id": hash(article.get("url", "")),
            "title": clean_text(article.get("title", "")),
            "content": cleaned_content,
            "url": article.get("url", ""),
            "source": article.get("source", "Unknown"),
            "published_at": article.get("published_at", ""),
            "query": article.get("query", "")
        })
    
    return processed


def save_articles(articles: List[Dict], filepath: str = "data/articles.json"):
    """Save articles to JSON file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(articles)} articles to {filepath}")


def load_articles(filepath: str = "data/articles.json") -> List[Dict]:
    """Load articles from JSON file"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_and_save():
    """Main function to fetch and save articles"""
    print("Fetching financial news articles...")
    raw_articles = fetch_news_articles()
    
    print("\nProcessing articles...")
    processed_articles = process_articles(raw_articles)
    
    print("\nSaving articles...")
    save_articles(processed_articles)
    
    return processed_articles


if __name__ == "__main__":
    fetch_and_save()
