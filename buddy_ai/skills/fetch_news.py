"""
Ultron News Fetcher (Titan Protocol)
Fetches live breaking news using public RSS feeds.
"""
import urllib.request
import xml.etree.ElementTree as ET

def fetch_breaking_news(topic="world"):
    """
    Fetches the latest breaking news headlines.
    Topic can be 'world', 'technology', 'business', or 'sports'.
    """
    try:
        # Use Google News RSS feeds as a reliable source without needing an API key
        topic_map = {
            "world": "w",
            "technology": "t",
            "business": "b",
            "sports": "s"
        }
        t = topic_map.get(topic.lower(), "w")
        url = f"https://news.google.com/news/rss/headlines/section/topic/{t.upper()}?hl=en-US&gl=US&ceid=US:en"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        items = root.findall('.//item')
        
        if not items:
            return "No news found for this topic at the moment."
            
        news_summary = f"--- BREAKING NEWS ({topic.upper()}) ---\n"
        for idx, item in enumerate(items[:5], 1): # Top 5 headlines
            title = item.find('title').text
            pub_date = item.find('pubDate').text
            news_summary += f"{idx}. {title}\n   (Published: {pub_date})\n\n"
            
        return news_summary
    except Exception as e:
        return f"Failed to fetch live news: {str(e)}"
