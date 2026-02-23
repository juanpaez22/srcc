# Stone Ranch Command Center - Agent Guidance

## Project Overview
A local home dashboard running on a Raspberry Pi (srcc.local) for LAN-only access. Built with Flask, designed for household use - something both users want to check every morning.

## Quick Start
```bash
# Deploy to Pi
ssh juanpaez@srcc.local "cd ~/dev/srcc && git pull && pkill -f app.py; nohup sudo python3 app.py > app.log 2>&1 &"

# Access at http://srcc.local
```

## Tech Stack
- **Backend**: Flask (Python)
- **APIs**: Open-Meteo (weather), Yahoo Finance (stocks), RSS feeds (news)
- **Storage**: JSON file (data.json) on Pi's filesystem
- **Frontend**: HTML/CSS/JS with vanilla JS (no framework)

## Key Files
- `app.py` - Main Flask application
- `config.py` - Configuration (weather location, stocks, news feeds)
- `data.json` - Persistent storage for chores and telemetry (auto-generated)
- `templates/` - HTML templates
- `static/` - CSS and images

## Important Notes

### Weather API
- Uses Open-Meteo (free, no key)
- Must use `&timezone=America/Los_Angeles` parameter to get times in local timezone
- Hourly forecast starts from current hour

### News Feeds
- Configured in `config.py`
- RSS feeds can be finicky - may need to handle different date formats
- Filter by last 24 hours using pubDate parsing

### Chores Scheduling
- Daily: every day
- Weekly: specify day of week (0-6, Monday=0)
- Bi-weekly: specify day of week, tracks 2-week intervals
- Monthly: specify day of month (1-28)
- Yearly: mm-dd format
- One time: yyyy-mm-dd

### Data Persistence
- Chores and telemetry stored in `data.json` in the app directory
- Persists across reboots
- Uses Flask's load_data() / save_data() helper functions

### Deployment
- Debug mode is OFF to prevent auto-reload issues
- Must manually restart after code updates
- Use `pkill -f app.py` then restart

### Pi-Specific
- Requires `sudo` for port 80
- pytz must be installed: `sudo pip3 install pytz --break-system-packages`

## Adding New Features
1. Add endpoint in `app.py`
2. Create template in `templates/` if new page needed
3. Add static assets to `static/`
4. Update `config.py` if configurable
5. Test locally first (port 5000 or 80)
6. Commit and push to GitHub
7. Pull on Pi and restart

## User Preferences (from conversation)
- Texas/Stone Ranch theme - burnt orange, tan, cream colors
- Longhorn logo (static/longhorn.png)
- Simplified tracker: workout (checkbox), sleep, mood (slider), drank (checkbox)
- Multi-user support for telemetry
- Stocks: MSFT, AMZN, GOOGL, AAPL, NVDA, TSLA
- Weather: Kirkland, WA
- News: World + Tech from multiple RSS sources
