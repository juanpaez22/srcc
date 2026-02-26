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

def calculate_streak(workouts, target=4):
    """Calculate current streak and weekly progress for gym/working out.
    target: workouts per week for streak
    Returns: {current_streak, weekly_count, weekly_target, weekly_progress_pct}"""
    if not workouts:
        return {'current_streak': 0, 'weekly_count': 0, 'weekly_target': target, 'weekly_progress_pct': 0}
    
    # Get dates of last 7 days
    today = datetime.now().date()
    week_dates = [(today - timedelta(days=i)).isoformat() for i in range(7)]
    
    # Count this week's workouts
    week_count = sum(1 for w in workouts if w.get('date', '')[:10] in week_dates)
    
    # Calculate streak - count consecutive days going backwards from today
    streak = 0
    check_date = today
    workout_dates = set(w.get('date', '')[:10] for w in workouts)
    
    while True:
        date_str = check_date.isoformat()
        if date_str in workout_dates:
            streak += 1
            check_date -= timedelta(days=1)
        elif check_date == today:
            # Today doesn't count yet, check yesterday
            check_date -= timedelta(days=1)
        else:
            break
        if streak > 365:  # Safety limit
            break
    
    return {
        'current_streak': streak,
        'weekly_count': week_count,
        'weekly_target': target,
        'weekly_progress_pct': min(100, int(week_count / target * 100))
    }

def calculate_achievements(workouts):
    """Calculate achievements/badges based on workout history.
    Returns list of unlocked achievements with details."""
    if not workouts:
        return []
    
    achievements = []
    total_workouts = len(workouts)
    
    # Get unique dates
    workout_dates = sorted(set(w.get('date', '')[:10] for w in workouts), reverse=True)
    
    # Calculate longest streak
    longest_streak = 0
    current_streak = 0
    prev_date = None
    
    for d in workout_dates:
        if prev_date:
            diff = (prev_date - datetime.strptime(d, '%Y-%m-%d').date()).days
            if diff == 1:
                current_streak += 1
            else:
                longest_streak = max(longest_streak, current_streak)
                current_streak = 1
        else:
            current_streak = 1
        prev_date = datetime.strptime(d, '%Y-%m-%d').date()
    longest_streak = max(longest_streak, current_streak)
    
    # Achievement definitions
    badges = [
        {'id': 'first_workout', 'name': 'First Step', 'desc': 'Completed your first workout', 'icon': '🌱', 'condition': total_workouts >= 1},
        {'id': 'five_workouts', 'name': 'Getting Started', 'desc': 'Completed 5 workouts', 'icon': '💪', 'condition': total_workouts >= 5},
        {'id': 'ten_workouts', 'name': 'Consistent', 'desc': 'Completed 10 workouts', 'icon': '🔥', 'condition': total_workouts >= 10},
        {'id': 'twenty_workouts', 'name': 'Dedicated', 'desc': 'Completed 20 workouts', 'icon': '⭐', 'condition': total_workouts >= 20},
        {'id': 'fifty_workouts', 'name': 'Beast Mode', 'desc': 'Completed 50 workouts', 'icon': '🦍', 'condition': total_workouts >= 50},
        {'id': 'streak_3', 'name': '3-Day Streak', 'desc': '3 days in a row', 'icon': '🎯', 'condition': longest_streak >= 3},
        {'id': 'streak_7', 'name': 'Week Warrior', 'desc': '7 days in a row', 'icon': '🗓️', 'condition': longest_streak >= 7},
        {'id': 'streak_14', 'name': 'Fortnight Fighter', 'desc': '14 days in a row', 'icon': '🛡️', 'condition': longest_streak >= 14},
        {'id': 'streak_30', 'name': 'Monthly Master', 'desc': '30 days in a row', 'icon': '👑', 'condition': longest_streak >= 30},
    ]
    
    for badge in badges:
        if badge['condition']:
            achievements.append({
                'id': badge['id'],
                'name': badge['name'],
                'desc': badge['desc'],
                'icon': badge['icon']
            })
    
    return {
        'achievements': achievements,
        'total_workouts': total_workouts,
        'longest_streak': longest_streak,
        'next_badge': next((b for b in badges if not b['condition']), None)
    }

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
    telemetry_data = data.get('telemetry', {})
    
    # Build entries list for read-only display
    entries = []
    for user, user_entries in telemetry_data.items():
        for entry in user_entries:
            entries.append({
                'user': user,
                'date': entry.get('date', 'Unknown'),
                'metrics': entry.get('metrics', {})
            })
    
    # Sort by date descending
    entries.sort(key=lambda x: x['date'], reverse=True)
    
    return render_template('telemetry.html', 
                          entries=entries[:50])  # Show last 50 entries

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

# Journaling system (git-ignored)
JOURNAL_FILE = os.path.join(os.path.dirname(__file__), 'data', 'journal.json')

JOURNAL_PROMPTS = [
    "What went well today?",
    "What challenged you?",
    "What are you grateful for?",
    "One thing you'd do differently tomorrow?",
    "How's your energy/mood?"
]

def load_journal():
    """Load journal entries"""
    if os.path.exists(JOURNAL_FILE):
        try:
            with open(JOURNAL_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'version': '1.0', 'entries': []}

def save_journal(data):
    """Save journal entries"""
    os.makedirs(os.path.dirname(JOURNAL_FILE), exist_ok=True)
    with open(JOURNAL_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/journal')
def journal():
    """Get all journal entries"""
    return load_journal()

@app.route('/journal/prompts')
def journal_prompts():
    """Get rotating journal prompts"""
    today_idx = datetime.now().toordinal() % len(JOURNAL_PROMPTS)
    return {'prompts': JOURNAL_PROMPTS, 'today': JOURNAL_PROMPTS[today_idx]}

@app.route('/journal', methods=['POST'])
def journal_entry():
    """Add a journal entry"""
    data = load_journal()
    
    entry = {
        'date': request.json.get('date', datetime.now().strftime('%Y-%m-%d')),
        'prompt': request.json.get('prompt', ''),
        'text': request.json.get('text', ''),
        'mood': request.json.get('mood')  # optional 1-10
    }
    data['entries'].append(entry)
    save_journal(data)
    return jsonify({'success': True, 'entry': entry})

# Push-model natural language logging
@app.route('/log', methods=['POST'])
def log_activity():
    """Parse natural language and log to appropriate life category.
    Gateway calls this for messages like 'I went to the gym', 'feeling great', etc."""
    text = (request.json.get('text', '') or '').lower()
    if not text:
        return jsonify({'success': False, 'error': 'No text provided'})
    
    today = datetime.now().strftime('%Y-%m-%d')
    logged = []
    
    life = load_life_data()
    
    # Fitness keywords
    fitness_kw = ['gym', 'workout', 'lift', 'ran', 'run', 'soccer', 'tennis', 'exercise', 'training', 'push day', 'leg day']
    if any(kw in text for kw in fitness_kw):
        workout = {
            'date': today,
            'type': 'gym' if 'gym' in text or 'lift' in text else ('run' if 'run' in text else 'workout'),
            'duration': 60,  # default
            'notes': text[:100]
        }
        life['fitness']['workouts'].append(workout)
        logged.append(f"workout logged")
    
    # Mood keywords
    mood_kw = {'great': 9, 'good': 7, 'okay': 5, 'meh': 4, 'bad': 2, 'terrible': 1, 'awesome': 10, 'amazing': 10}
    for kw, val in mood_kw.items():
        if kw in text:
            entry = {'date': today, 'mood': val, 'notes': text[:100]}
            life['mood']['entries'].append(entry)
            logged.append(f"mood: {val}/10")
            break
    
    # Learning keywords
    learn_kw = ['read', 'book', 'course', 'learned', 'studied', 'article']
    if any(kw in text for kw in learn_kw):
        item = {'date': today, 'type': 'book' if 'book' in text else 'article', 'title': text[:50], 'notes': ''}
        if 'books' not in life['learning']:
            life['learning']['books'] = []
        life['learning']['books'].append(item)
        logged.append("learning item logged")
    
    # Social keywords
    social_kw = ['hung out', 'met', 'call', 'dinner', 'lunch', 'coffee', 'friend', 'family']
    if any(kw in text for kw in social_kw):
        interaction = {'date': today, 'type': 'friend', 'with': text[:30], 'notes': ''}
        life['social']['interactions'].append(interaction)
        logged.append("social interaction logged")
    
    if logged:
        save_life_data(life)
        
        # Build friendly response
        response_msg = "Got it! "
        
        if 'workout logged' in logged:
            # Calculate streak for workout
            streak_info = calculate_streak(life.get('fitness', {}).get('workouts', []))
            streak = streak_info.get('current_streak', 0)
            week_count = streak_info.get('weekly_count', 0)
            target = streak_info.get('weekly_target', 4)
            
            if streak > 0:
                response_msg += f"🏋️ Workout recorded! 🔥 {streak}-day streak! ({week_count}/{target} this week) "
            else:
                response_msg += f"🏋️ Workout recorded! ({week_count}/{target} this week) "
        
        if 'mood:' in str(logged):
            response_msg += "😊 Mood noted! "
        
        if 'learning item logged' in logged:
            response_msg += "📚 Learning logged! "
        
        if 'social interaction logged' in logged:
            response_msg += "👥 Social time recorded! "
        
        return jsonify({'success': True, 'logged': logged, 'message': response_msg.strip()})
    
    return jsonify({'success': False, 'message': "Didn't recognize that activity. Try: 'went to gym', 'feeling great', 'read a book', 'hung out with friend'"})

@app.route('/life/streaks')
def life_streaks():
    """Get streak info for fitness and other tracked activities"""
    data = load_life_data()
    fitness = data.get('fitness', {})
    workouts = fitness.get('workouts', [])
    
    # Get weekly gym target (default 4)
    target = fitness.get('goals', {}).get('weekly_gym_target', 4)
    
    streak = calculate_streak(workouts, target)
    achievements = calculate_achievements(workouts)
    
    return jsonify({
        'fitness': streak,
        'achievements': achievements,
        'goals': fitness.get('goals', {})
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
