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

## Features

- System telemetry (CPU/Memory usage)
- Weather for Kirkland, WA
- Extensible widget architecture

## Tech Stack

- Flask (Python)
- psutil for system stats
- Open-Meteo API (free, no key required)

## Development

```
srcc/
├── app.py           # Flask backend
├── templates/
│   └── index.html   # Main dashboard
└── static/
    └── style.css    # Styles
```
