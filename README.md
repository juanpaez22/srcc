# Stone Ranch Command Center

A local home dashboard running on a Raspberry Pi.

## Quick Start

```bash
# Install dependencies
pip install flask psutil requests

# Run locally
python app.py

# Deploy to Pi
# - Clone repo to Pi: git clone https://github.com/juanpaez22/srcc.git ~/dev/srcc
# - Run: sudo python3 ~/dev/srcc/app.py
# - Access at http://srcc.local
```

## Configuration

Edit `config.py` to customize:
- Weather location (latitude, longitude, city name)
- News feeds (RSS URLs)
- Refresh intervals

## Features

- **Weather**: Current conditions + hourly forecast for today
- **News**: World and tech news from RSS feeds (last 24 hours)
- **Chores**: Schedule recurring chores with flexible timing
- **Tracker**: Daily habit/mood/productivity logging
- **System Telemetry**: CPU/Memory monitoring

## Pages

- `/` - Main dashboard
- `/chores_page` - Manage chores
- `/telemetry` - Daily tracker

## Tech Stack

- Flask (Python)
- psutil for system stats
- Open-Meteo API (free, no key required)
- RSS feeds for news

## Project Structure

```
srcc/
├── app.py           # Flask backend
├── config.py        # Configuration
├── data.json        # Chores & telemetry data (created automatically)
├── templates/
│   ├── index.html   # Main dashboard
│   ├── chores.html  # Chores management
│   └── telemetry.html # Daily tracker
└── static/
    └── style.css    # Styles
```
