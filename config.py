# Stone Ranch Command Center - Configuration

# Weather location (Kirkland, WA)
WEATHER_LAT = 47.6769
WEATHER_LON = -122.2060
WEATHER_CITY = "Kirkland, WA"

# Stocks to track (Yahoo Finance symbols)
STOCKS = ["MSFT", "AMZN", "GOOGL", "AAPL", "NVDA", "TSLA"]

# News feeds (RSS URLs) - at least 2-3 sources per category
NEWS_FEEDS = {
    "world": {
        "title": "World News",
        "feeds": [
            "https://feeds.bbci.co.uk/news/world/rss.xml",
            "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"
        ]
    },
    "tech": {
        "title": "Tech News",
        "feeds": [
            "https://techcrunch.com/feed/",
            "https://www.theverge.com/rss/index.xml",
            "https://www.wired.com/feed/rss"
        ]
    },
    "sports": {
        "title": "Sports",
        "feeds": [
            "https://www.espn.com/espn/rss/news",
            "https://sports.yahoo.com/rss/",
            "https://rss.nytimes.com/services/xml/rss/nyt/Sports.xml"
        ]
    },
    "soccer": {
        "title": "Soccer",
        "feeds": [
            "https://www.goal.com/en-us/feeds/rss/news",
            "https://www.espn.com/soccer/rss/_/league/all"
        ]
    }
}

# Team-specific feeds (for personalized digest)
TEAM_FEEDS = {
    "texas_longhorns": {
        "name": "Texas Longhorns",
        "search": "Texas Longhorns football",
        "feeds": [
            "https://www.espn.com/college-football/team/_/id/239/texas-longhorns"
        ]
    },
    "man_united": {
        "name": "Manchester United",
        "search": "Manchester United",
        "feeds": [
            "https://www.manutd.com/rss/news"
        ]
    },
    "real_madrid": {
        "name": "Real Madrid",
        "search": "Real Madrid",
        "feeds": [
            "https://www.realmadrid.com/en/rss"
        ]
    }
}

# Dashboard refresh intervals (milliseconds)
REFRESH_INTERVAL_STATS = 3000
REFRESH_INTERVAL_WEATHER = 300000  # 5 minutes
REFRESH_INTERVAL_NEWS = 300000     # 5 minutes
REFRESH_INTERVAL_STOCKS = 60000    # 1 minute

# Default chores (used if data.json has none)
# schedule: daily, weekly, monthly, yearly, onetime
# schedule_param: for weekly="weeks,day" (e.g., "1,0"=every Mon), monthly=day(1-31), yearly="mm-dd", onetime="yyyy-mm-dd"
DEFAULT_CHORES = [
    {"name": "Check weather station", "schedule": "daily", "schedule_param": ""},
    {"name": "Review security cameras", "schedule": "daily", "schedule_param": ""},
    {"name": "Backup system logs", "schedule": "weekly", "schedule_param": "1,6"},
    {"name": "Check smoke detectors", "schedule": "monthly", "schedule_param": "1"},
    {"name": "Clean solar panels", "schedule": "weekly", "schedule_param": "1,0"}
]
