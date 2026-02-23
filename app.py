from flask import Flask, render_template, request, jsonify, redirect, url_for
import psutil
import time
import requests
import json
import os
from datetime import datetime, timedelta
from config import WEATHER_LAT, WEATHER_LON, WEATHER_CITY, NEWS_FEEDS, STOCKS

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data.json')

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {'chores': [], 'telemetry': {}, 'users': ['Default']}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def get_weather():
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={WEATHER_LAT}&longitude={WEATHER_LON}&current=temperature_2m,weather_code,wind_speed_10m&hourly=temperature_2m,weather_code&forecast_days=1"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        
        current = data.get('current', {})
        hourly = data.get('hourly', {})
        
        temp_f = round(current.get('temperature_2m', 0) * 9/5 + 32)
        wind = current.get('wind_speed_10m', 0)
        code = current.get('weather_code', 0)
        
        now = datetime.now()
        current_hour = now.hour
        hourly_times = hourly.get('time', [])
        hourly_temps = hourly.get('temperature_2m', [])
        hourly_codes = hourly.get('weather_code', [])
        
        forecast = []
        for i, t in enumerate(hourly_times):
            dt = datetime.fromisoformat(t.replace('Z', '+00:00'))
            # Show hours from current local time onwards (next 24h)
            if dt.hour >= current_hour and dt.day == now.day:
                temp_c = hourly_temps[i] if i < len(hourly_temps) else 0
                forecast.append({
                    'time': dt.strftime('%I %p'),
                    'temp': round(temp_c * 9/5 + 32),
                    'code': hourly_codes[i] if i < len(hourly_codes) else 0
                })
                if len(forecast) >= 6:
                    break
        
        # If no forecast for today, get tomorrow's
        if not forecast:
            for i, t in enumerate(hourly_times):
                dt = datetime.fromisoformat(t.replace('Z', '+00:00'))
                temp_c = hourly_temps[i] if i < len(hourly_temps) else 0
                forecast.append({
                    'time': dt.strftime('%I %p'),
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
                elif 'techcrunch' in feed_url:
                    source = "TechCrunch"
                elif 'verge' in feed_url:
                    source = "The Verge"
                elif 'reuters' in feed_url:
                    source = "Reuters"
                
                import re
                items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
                
                for item in items[:8]:
                    title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>', item)
                    link_match = re.search(r'<link>(.*?)</link>', item)
                    pub_match = re.search(r'<pubDate>(.*?)</pubDate>', item)
                    
                    title = (title_match.group(1) or title_match.group(2) or "No title").strip()
                    link = link_match.group(1).strip() if link_match else "#"
                    pub_date = pub_match.group(1).strip() if pub_match else ""
                    
                    if title not in seen_titles and len(articles) < 20:
                        try:
                            pub_dt = datetime.strptime(pub_date[:25], '%a, %d %b %Y %H:%M:%S')
                            pub_dt = pub_dt.replace(tzinfo=None)
                            if (datetime.now() - pub_dt).days <= 1:
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
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    today_dow = today.weekday()
    
    chores = []
    for chore in data.get('chores', []):
        schedule = chore.get('schedule', 'weekly')
        last_done = chore.get('last_done', '')
        
        should_show = False
        
        if schedule == 'daily':
            should_show = True
        elif schedule == 'weekly':
            if today_dow == 6:  # Sunday
                should_show = True
        elif schedule == 'biweekly':
            if today_dow == 6:
                if last_done:
                    try:
                        last = datetime.strptime(last_done, '%Y-%m-%d')
                        if (today - last).days >= 14:
                            should_show = True
                    except:
                        should_show = True
                else:
                    should_show = True
        elif schedule == 'monthly':
            if today_dow == 6 and today.day <= 7:
                if last_done:
                    try:
                        last = datetime.strptime(last_done, '%Y-%m-%d')
                        if (today - last).days >= 30:
                            should_show = True
                    except:
                        should_show = True
                else:
                    should_show = True
        
        if should_show:
            chores.append(chore['name'])
    
    return chores

def get_yesterday_checkin_status():
    data = load_data()
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    users = data.get('users', ['Default'])
    telemetry = data.get('telemetry', {})
    
    missing = []
    for user in users:
        if yesterday not in telemetry.get(user, []):
            missing.append(user)
    
    return yesterday, missing

@app.route('/')
def index():
    yesterday, missing_users = get_yesterday_checkin_status()
    return render_template('index.html', 
                           weather_city=WEATHER_CITY,
                           yesterday=yesterday,
                           missing_users=missing_users)

@app.route('/stats')
def stats():
    return {
        'cpu': psutil.cpu_percent(),
        'memory': psutil.virtual_memory().percent,
        'time': time.strftime('%H:%M:%S')
    }

@app.route('/weather')
def weather():
    return get_weather()

@app.route('/news')
def news():
    return {'articles': get_news()}

@app.route('/stocks')
def stocks():
    return {'stocks': get_stocks()}

@app.route('/chores')
def chores():
    return {'chores': get_today_chores()}

@app.route('/checkin_status')
def checkin_status():
    yesterday, missing_users = get_yesterday_checkin_status()
    return {'yesterday': yesterday, 'missing_users': missing_users}

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
            chore = {
                'name': request.form.get('name'),
                'schedule': request.form.get('schedule'),
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
