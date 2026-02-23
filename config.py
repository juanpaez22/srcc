# Stone Ranch Command Center - Configuration

# Weather location (Kirkland, WA)
WEATHER_LAT = 47.6769
WEATHER_LON = -122.2060
WEATHER_CITY = "Kirkland, WA"

# News feeds (RSS URLs)
NEWS_FEEDS = {
    "world": {
        "title": "World News",
        "feeds": [
            "https://feeds.reuters.com/reuters/topNews",
            "https://feeds.bbci.co.uk/news/world/rss.xml"
        ]
    },
    "tech": {
        "title": "Tech News",
        "feeds": [
            "https://techcrunch.com/feed/",
            "https://www.theverge.com/rss/index.xml"
        ]
    }
}

# Dashboard refresh intervals (milliseconds)
REFRESH_INTERVAL_STATS = 3000
REFRESH_INTERVAL_WEATHER = 300000  # 5 minutes
REFRESH_INTERVAL_NEWS = 300000     # 5 minutes
