# Stone Ranch Command Center (SRCC)

A local home dashboard running on a Raspberry Pi 3B+ for LAN-only access.

## Project Ideas

### Quick-glance status
- Family calendar (Google/Outlook)
- Weather + forecast
- Network status (devices home, VPN, Pi stats)
- Download queue

### Morning routine
- Today's agenda summary
- Commute time / weather
- Top news headlines

### Household coordination
- Shared grocery/shopping list
- Chore rotation chart
- Meal plan
- Shared notes board

### Background useful
- Gmail unread count + sender preview
- GitHub notifications
- Stocks/crypto portfolio
- Package tracking

### Fun extras
- Wikipedia article of the day
- Today's XKCD
- Random quote generator

## Current Status

### POC Phase
Building a minimal Flask dashboard showing CPU and memory usage to test the stack and LAN deployment.

### Tech Stack
- Flask (Python)
- psutil for system stats
- Single HTML page with JS polling

### To Deploy to Pi
```bash
scp -r ~/Desktop/Projects/srcc pi@<pi-ip>:~/
ssh pi@<pi-ip>
cd srcc
pip install flask psutil
python app.py
```

Then access at `http://<pi-ip>:5000` on your local network.
