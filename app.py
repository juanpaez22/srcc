from flask import Flask, render_template, request, jsonify, redirect, url_for
import psutil
import time
import requests
import json
import os
from datetime import datetime, timedelta, timezone
import pytz
from config import WEATHER_LAT, WEATHER_LON, WEATHER_CITY, NEWS_FEEDS, STOCKS, DEFAULT_CHORES

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data.json')
PACIFIC_TZ = pytz.timezone('America/Los_Angeles')

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {'chores': [], 'telemetry': {}, 'users': ['Default']}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

# Life data (fitness, mood, learning, social) - git-ignored
LIFE_FILE = os.path.join(os.path.dirname(__file__), 'data', 'life.json')

def load_life_data():
    """Load personal life tracking data (fitness, mood, learning, social)"""
    if os.path.exists(LIFE_FILE):
        try:
            with open(LIFE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        'version': '1.0',
        'fitness': {'workouts': [], 'goals': {'weekly_gym_target': 4, 'primary': 'Build strength and muscle mass'}},
        'mood': {'entries': []},
        'learning': {'books': [], 'courses': [], 'skills': []},
        'social': {'interactions': []}
    }

def save_life_data(data):
    """Save personal life tracking data"""
    os.makedirs(os.path.dirname(LIFE_FILE), exist_ok=True)
    with open(LIFE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_weather():
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={WEATHER_LAT}&longitude={WEATHER_LON}&current=temperature_2m,weather_code,wind_speed_10m&hourly=temperature_2m,weather_code&forecast_days=2&timezone=America/Los_Angeles"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        
        current = data.get('current', {})
        hourly = data.get('hourly', {})
        
        temp_f = round(current.get('temperature_2m', 0) * 9/5 + 32)
        wind = current.get('wind_speed_10m', 0)
        code = current.get('weather_code', 0)
        
        now_pacific = datetime.now(PACIFIC_TZ)
        hourly_times = hourly.get('time', [])
        hourly_temps = hourly.get('temperature_2m', [])
        hourly_codes = hourly.get('weather_code', [])
        
        forecast = []
        
        # Show the next 6 hours from now
        # Times from API are now in local Pacific time
        for i, t in enumerate(hourly_times):
            dt_local = datetime.fromisoformat(t)
            dt_local = PACIFIC_TZ.localize(dt_local)
            
            # Only include hours that are >= now
            if dt_local >= now_pacific:
                temp_c = hourly_temps[i] if i < len(hourly_temps) else 0
                forecast.append({
                    'time': dt_local.strftime('%I %p'),
                    'temp': round(temp_c * 9/5 + 32),
                    'code': hourly_codes[i] if i < len(hourly_codes) else 0
                })
                if len(forecast) >= 6:
                    break
        
        conditions = {
            0: "Clear", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
            45: "Fog", 48: "Fog",
            51: "Drizzle", 53: "Drizzle", 55: "Drizzle",
            61: "Rain", 63: "Rain", 65: "Rain",
            71: "Snow", 73: "Snow", 75: "Snow",
            80: "Showers", 81: "Showers", 82: "Showers",
            95: "Thunderstorm", 96: "Thunderstorm"
        }
        
        return {
            'temp': temp_f,
            'condition': conditions.get(code, "Unknown"),
            'wind': round(wind * 0.621371),
            'city': WEATHER_CITY,
            'forecast': forecast,
            'error': None
        }
    except Exception as e:
        return {'temp': '--', 'condition': '--', 'wind': '--', 'city': WEATHER_CITY, 'forecast': [], 'error': str(e)}

def get_news():
    """Fetch news from RSS feeds, handling both RSS and Atom formats."""
    articles = []
    seen_titles = set()
    
    for category, config in NEWS_FEEDS.items():
        for feed_url in config['feeds']:
            try:
                resp = requests.get(feed_url, timeout=5)
                content = resp.text
                
                source = ""
                if 'bbc' in feed_url:
                    source = "BBC"
                elif 'reuters' in feed_url:
                    source = "Reuters"
                elif 'nytimes' in feed_url:
                    source = "NYT"
                elif 'techcrunch' in feed_url:
                    source = "TechCrunch"
                elif 'verge' in feed_url:
                    source = "The Verge"
                elif 'wired' in feed_url:
                    source = "Wired"
                
                import re
                
                # Try RSS <item> first, then Atom <entry>
                items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
                if not items:
                    items = re.findall(r'<entry>(.*?)</entry>', content, re.DOTALL)
                
                for item in items[:8]:
                    # Handle both RSS and Atom title formats
                    title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>', item)
                    # Handle both RSS <link> and Atom <link href="...">
                    link_match = re.search(r'<link>(.*?)</link>|<link href="([^"]+)"', item)
                    pub_match = re.search(r'<pubDate>(.*?)</pubDate>|<published>(.*?)</published>', item)
                    
                    title = (title_match.group(1) or title_match.group(2) or "No title").strip() if title_match else "No title"
                    link = (link_match.group(1) or link_match.group(2) or "#").strip() if link_match else "#"
                    pub_date = (pub_match.group(1) or pub_match.group(2) or "").strip() if pub_match else ""
                    
                    if title not in seen_titles and len(articles) < 20:
                        try:
                            # Try multiple date formats (strip timezone for simpler parsing)
                            pub_dt = None
                            pub_clean = re.sub(r'[A-Z]{2,4}$', '', pub_date[:25]).strip()
                            for fmt in ['%a, %d %b %Y %H:%M:%S', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S']:
                                try:
                                    pub_dt = datetime.strptime(pub_clean, fmt)
                                    break
                                except:
                                    continue
                            if pub_dt and (datetime.now() - pub_dt.replace(tzinfo=None)).days <= 1:
                                articles.append({
                                    'title': title[:75] + ('...' if len(title) > 75 else ''),
                                    'link': link,
                                    'category': category,
                                    'source': source
                                })
                                seen_titles.add(title)
                        except:
                            pass
            except:
                continue
    
    return articles

def get_ai_digest(cached=False):
    """Generate an AI-style digest by clustering news into themes.
    Uses extractive ranking - no external API needed. Pi-friendly.
    If cached=True, reads from cache file."""
    import re
    
    cache_file = os.path.join(os.path.dirname(__file__), 'digest_cache.json')
    
    if cached and os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except:
            pass
    
    articles = get_news()
    if not articles:
        return {'themes': [], 'error': 'No news available'}
    
    # Keywords for clustering
    theme_keywords = {
        'Politics & Government': ['trump', 'biden', 'congress', 'senate', 'white house', 'election', 'policy', 'government', 'parliament', 'minister'],
        'Tech & AI': ['ai', 'artificial intelligence', 'tech', 'google', 'microsoft', 'apple', 'meta', 'facebook', 'amazon', 'startup', 'chip', 'semiconductor'],
        'World': ['china', 'russia', 'ukraine', 'europe', 'middle east', 'war', 'military', 'nato', 'korea', 'india'],
        'Business & Economy': ['economy', 'market', 'stock', 'inflation', 'fed', 'interest', 'trade', 'oil', 'energy', 'gas', 'price'],
        'Science & Health': ['space', 'nasa', 'health', 'covid', 'vaccine', 'disease', 'cancer', 'climate', 'weather', 'storm'],
    }
    
    # Assign articles to themes
    themed = {theme: [] for theme in theme_keywords}
    themed['Other'] = []
    
    for article in articles:
        title_lower = article['title'].lower()
        assigned = False
        for theme, keywords in theme_keywords.items():
            if any(kw in title_lower for kw in keywords):
                themed[theme].append(article)
                assigned = True
                break
        if not assigned:
            themed['Other'].append(article)
    
    # Build digest with top headlines per theme
    digest_themes = []
    for theme, items in themed.items():
        if items:
            # Pick top 3 articles per theme
            top_items = items[:3]
            digest_themes.append({
                'theme': theme,
                'headlines': [{'title': a['title'], 'link': a['link'], 'source': a['source']} for a in top_items]
            })
    
    return {'themes': digest_themes, 'error': None}

def get_stocks():
    results = []
    for symbol in STOCKS:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=5)
            data = resp.json()
            
            result = data.get('chart', {}).get('result', [])
            if not result:
                continue
                
            meta = result[0].get('meta', {})
            price = meta.get('regularMarketPrice', 0)
            prev_close = meta.get('chartPreviousClose', price)
            change = price - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0
            
            results.append({
                'symbol': symbol,
                'name': meta.get('shortName', symbol)[:15] if meta.get('shortName') else symbol,
                'price': round(price, 2),
                'change': round(change, 2),
                'change_pct': round(change_pct, 2)
            })
        except:
            continue
    
    return results

def get_today_chores():
    data = load_data()
    # Use default chores if none defined in data.json
    chores_data = data.get('chores', []) or DEFAULT_CHORES
    
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    today_dow = today.weekday()  # 0=Monday, 6=Sunday
    today_dom = today.day
    
    chores = []
    for chore in chores_data:
        schedule = chore.get('schedule', 'daily')
        schedule_param = chore.get('schedule_param', '')
        last_done = chore.get('last_done', '')
        
        should_show = False
        
        if schedule == 'daily':
            should_show = True
            
        elif schedule == 'weekly':
            # schedule_param is "weeks,day" e.g., "2,0" = every 2 weeks on Monday
            if ',' in schedule_param:
                parts = schedule_param.split(',')
                weeks = int(parts[0]) if parts[0] else 1
                target_dow = int(parts[1]) if len(parts) > 1 else 6
            else:
                weeks = 1
                target_dow = int(schedule_param) if schedule_param else 6
            
            if today_dow == target_dow:
                if last_done:
                    try:
                        last = datetime.strptime(last_done, '%Y-%m-%d')
                        if (today - last).days >= (weeks * 7):
                            should_show = True
                    except:
                        should_show = True
                else:
                    should_show = True
                    
        elif schedule == 'monthly':
            # schedule_param is day of month (1-31)
            target_dom = int(schedule_param) if schedule_param else 1
            if today_dom == target_dom:
                if last_done:
                    try:
                        last = datetime.strptime(last_done, '%Y-%m-%d')
                        if (today - last).days >= 30:
                            should_show = True
                    except:
                        should_show = True
                else:
                    should_show = True
                    
        elif schedule == 'yearly':
            # schedule_param is mm-dd
            if schedule_param:
                month_day = today.strftime('%m-%d')
                if month_day == schedule_param:
                    should_show = True
                    
        elif schedule == 'onetime':
            # schedule_param is yyyy-mm-dd
            if schedule_param == today_str:
                should_show = True
        
        if should_show:
            chores.append(chore['name'])
    
    return chores

def get_overdue_chores():
    """Get chores that were due but not completed"""
    data = load_data()
    # Use default chores if none defined in data.json
    chores_data = data.get('chores', []) or DEFAULT_CHORES
    
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    today_dow = today.weekday()
    today_dom = today.day
    
    overdue = []
    for chore in chores_data:
        # Skip if already done today
        if chore.get('last_done', '') == today_str:
            continue
            
        schedule = chore.get('schedule', 'daily')
        schedule_param = chore.get('schedule_param', '')
        last_done = chore.get('last_done', '')
        
        # Check if it was due on any previous day
        was_due = False
        
        if schedule == 'daily':
            was_due = True  # All daily chores are overdue if not done today
        elif schedule == 'weekly':
            if ',' in schedule_param:
                parts = schedule_param.split(',')
                target_dow = int(parts[1]) if len(parts) > 1 else 6
            else:
                target_dow = int(schedule_param) if schedule_param else 6
            # Check if the target day was earlier this week
            if today_dow > target_dow:
                was_due = True
        elif schedule == 'monthly':
            target_dom = int(schedule_param) if schedule_param else 1
            if today_dom > target_dom:
                was_due = True
        elif schedule == 'yearly':
            if schedule_param:
                month_day = today.strftime('%m-%d')
                if month_day > schedule_param:
                    was_due = True
        elif schedule == 'onetime':
            if schedule_param and schedule_param < today_str:
                was_due = True
        
        if was_due:
            overdue.append(chore['name'])
    
    return overdue

def get_yesterday_checkin_status():
    data = load_data()
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    users = data.get('users', ['Default'])
    telemetry = data.get('telemetry', {})
    
    missing = []
    completed = []
    for user in users:
        user_entries = telemetry.get(user, [])
        has_entry = any(entry.get('date') == yesterday for entry in user_entries)
        if has_entry:
            completed.append(user)
        else:
            missing.append(user)
    
    return yesterday, missing, completed

@app.route('/')
def index():
    yesterday, missing_users, completed_users = get_yesterday_checkin_status()
    return render_template('index.html', 
                           weather_city=WEATHER_CITY,
                           yesterday=yesterday,
                           missing_users=missing_users,
                           completed_users=completed_users)

@app.route('/stats')
def stats():
    data = load_data()
    return {
        'cpu': psutil.cpu_percent(),
        'memory': psutil.virtual_memory().percent,
        'time': time.strftime('%H:%M:%S'),
        'last_tend_time': data.get('last_tend_time', '')
    }

@app.route('/tend', methods=['POST'])
def tend():
    """Update the last Bevo tend time (heartbeat)"""
    data = load_data()
    data['last_tend_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    save_data(data)
    return jsonify({'success': True, 'last_tend_time': data['last_tend_time']})

@app.route('/weather')
def weather():
    return get_weather()

@app.route('/news')
def news():
    return {'articles': get_news()}

@app.route('/digest')
def digest():
    """AI-style digest - grouped by themes (uses cached version)"""
    return get_ai_digest(cached=True)

@app.route('/digest-cache', methods=['POST'])
def digest_cache():
    """Generate and cache the digest (for cron job at 5am)"""
    result = get_ai_digest(cached=False)
    cache_file = os.path.join(os.path.dirname(__file__), 'digest_cache.json')
    with open(cache_file, 'w') as f:
        json.dump(result, f)
    return jsonify({'success': True, 'cached_at': datetime.now().isoformat()})

@app.route('/stocks')
def stocks():
    return {'stocks': get_stocks()}

@app.route('/chores')
def chores():
    return {'chores': get_today_chores(), 'overdue': get_overdue_chores()}

@app.route('/checkin_status')
def checkin_status():
    yesterday, missing_users, completed_users = get_yesterday_checkin_status()
    return {'yesterday': yesterday, 'missing_users': missing_users, 'completed_users': completed_users}

@app.route('/telemetry', methods=['GET', 'POST'])
def telemetry():
    data = load_data()
    users = data.get('users', ['Default'])
    
    if request.method == 'POST':
        action = request.form.get('action') or request.json.get('action') if request.json else None
        
        if action == 'add_user':
            new_user = request.form.get('new_user') or (request.json.get('new_user') if request.json else None)
            if new_user and new_user not in users:
                users.append(new_user)
                data['users'] = users
                if new_user not in data.get('telemetry', {}):
                    data['telemetry'][new_user] = []
                save_data(data)
                return jsonify({'success': True, 'users': users})
        
        # Submit check-in
        user = request.form.get('user') or (request.json.get('user') if request.json else None)
        date = request.form.get('date') or (request.json.get('date') if request.json else None)
        
        if not user:
            user = users[0]
        if not date:
            date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        metrics = {}
        if request.form:
            metrics = {k: v for k, v in request.form.items() if k not in ['action', 'user', 'date']}
        elif request.json:
            metrics = request.json.get('metrics', {})
        
        if user not in data.get('telemetry', {}):
            data['telemetry'][user] = []
        
        # Remove existing entry for this date
        data['telemetry'][user] = [e for e in data['telemetry'][user] if e.get('date') != date]
        
        entry = {'date': date, 'metrics': metrics}
        data['telemetry'][user].append(entry)
        save_data(data)
        return jsonify({'success': True})
    
    # GET - show form
    telemetry_data = data.get('telemetry', {})
    return render_template('telemetry.html', 
                          users=users, 
                          telemetry=telemetry_data,
                          yesterday=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))

@app.route('/chores_page', methods=['GET', 'POST'])
def chores_page():
    data = load_data()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            schedule = request.form.get('schedule')
            schedule_param = request.form.get('schedule_param', '')
            
            # Handle weekly (every N weeks)
            if schedule == 'weekly':
                weeks = request.form.get('schedule_weeks', '1')
                day = request.form.get('schedule_param', '6')
                schedule_param = f"{weeks},{day}"  # e.g., "2,0" = every 2 weeks on Monday
            
            # Handle yearly (mm-dd)
            elif schedule == 'yearly':
                month = request.form.get('schedule_month', '01')
                day = request.form.get('schedule_day', '01')
                schedule_param = f"{month}-{day}"
            
            chore = {
                'name': request.form.get('name'),
                'schedule': schedule,
                'schedule_param': schedule_param,
                'last_done': ''
            }
            data['chores'].append(chore)
        
        elif action == 'complete':
            idx = int(request.form.get('index'))
            if idx < len(data['chores']):
                data['chores'][idx]['last_done'] = datetime.now().strftime('%Y-%m-%d')
        
        elif action == 'delete':
            idx = int(request.form.get('index'))
            if idx < len(data['chores']):
                data['chores'].pop(idx)
        
        save_data(data)
    
    return render_template('chores.html', chores=data.get('chores', []))

@app.route('/complete_chore/<int:index>')
def complete_chore(index):
    data = load_data()
    if index < len(data['chores']):
        data['chores'][index]['last_done'] = datetime.now().strftime('%Y-%m-%d')
        save_data(data)
    return redirect(url_for('chores_page'))

@app.route('/delete_chore/<int:index>')
def delete_chore(index):
    data = load_data()
    if index < len(data['chores']):
        data['chores'].pop(index)
        save_data(data)
    return redirect(url_for('chores_page'))

# Life tracking endpoints (fitness, mood, learning, social)
@app.route('/life')
def life():
    """Get all life data"""
    return load_life_data()

@app.route('/life/fitness', methods=['GET', 'POST'])
def life_fitness():
    """Log or get fitness data"""
    data = load_life_data()
    
    if request.method == 'POST':
        workout = {
            'date': request.json.get('date', datetime.now().strftime('%Y-%m-%d')),
            'type': request.json.get('type', 'gym'),
            'duration': request.json.get('duration'),
            'notes': request.json.get('notes', '')
        }
        data['fitness']['workouts'].append(workout)
        save_life_data(data)
        return jsonify({'success': True, 'workout': workout})
    
    return jsonify(data.get('fitness', {}))

@app.route('/life/mood', methods=['GET', 'POST'])
def life_mood():
    """Log or get mood data"""
    data = load_life_data()
    
    if request.method == 'POST':
        entry = {
            'date': request.json.get('date', datetime.now().strftime('%Y-%m-%d')),
            'mood': request.json.get('mood'),  # 1-10 scale
            'notes': request.json.get('notes', '')
        }
        data['mood']['entries'].append(entry)
        save_life_data(data)
        return jsonify({'success': True, 'entry': entry})
    
    return jsonify(data.get('mood', {}))

@app.route('/life/learning', methods=['GET', 'POST'])
def life_learning():
    """Log or get learning data"""
    data = load_life_data()
    
    if request.method == 'POST':
        item = {
            'date': request.json.get('date', datetime.now().strftime('%Y-%m-%d')),
            'type': request.json.get('type', 'book'),  # book, course, skill
            'title': request.json.get('title'),
            'notes': request.json.get('notes', '')
        }
        item_type = item['type'] + 's'  # books, courses, skills
        if item_type not in data['learning']:
            data['learning'][item_type] = []
        data['learning'][item_type].append(item)
        save_life_data(data)
        return jsonify({'success': True, 'item': item})
    
    return jsonify(data.get('learning', {}))

@app.route('/life/social', methods=['GET', 'POST'])
def life_social():
    """Log or get social data"""
    data = load_life_data()
    
    if request.method == 'POST':
        interaction = {
            'date': request.json.get('date', datetime.now().strftime('%Y-%m-%d')),
            'type': request.json.get('type', 'friend'),  # family, friend, colleague
            'with': request.json.get('with'),
            'notes': request.json.get('notes', '')
        }
        data['social']['interactions'].append(interaction)
        save_life_data(data)
        return jsonify({'success': True, 'interaction': interaction})
    
    return jsonify(data.get('social', {}))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
