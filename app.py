from flask import Flask, render_template, request, jsonify, redirect, url_for
import psutil
import time
import requests
import json
import os
from datetime import datetime, timedelta
from config import WEATHER_LAT, WEATHER_LON, WEATHER_CITY, NEWS_FEEDS

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data.json')

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {'chores': [], 'telemetry': []}

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
        hourly_times = hourly.get('time', [])
        hourly_temps = hourly.get('temperature_2m', [])
        hourly_codes = hourly.get('weather_code', [])
        
        forecast = []
        for i, t in enumerate(hourly_times):
            dt = datetime.fromisoformat(t.replace('Z', '+00:00'))
            if dt >= now:
                temp_c = hourly_temps[i] if i < len(hourly_temps) else 0
                forecast.append({
                    'time': dt.strftime('%I %p'),
                    'temp': round(temp_c * 9/5 + 32),
                    'code': hourly_codes[i] if i < len(hourly_codes) else 0
                })
                if len(forecast) >= 8:
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
            'forecast': forecast[:6],
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
                
                import re
                items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
                
                for item in items[:5]:
                    title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>', item)
                    link_match = re.search(r'<link>(.*?)</link>', item)
                    pub_match = re.search(r'<pubDate>(.*?)</pubDate>', item)
                    
                    title = (title_match.group(1) or title_match.group(2) or "No title").strip()
                    link = link_match.group(1).strip() if link_match else "#"
                    pub_date = pub_match.group(1).strip() if pub_match else ""
                    
                    if title not in seen_titles and len(articles) < 15:
                        try:
                            pub_dt = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
                            if (datetime.now(pub_dt.tzinfo) - pub_dt).days <= 1:
                                articles.append({
                                    'title': title[:80] + ('...' if len(title) > 80 else ''),
                                    'link': link,
                                    'category': category
                                })
                                seen_titles.add(title)
                        except:
                            pass
            except:
                continue
    
    return articles

def get_today_chores():
    data = load_data()
    today = datetime.now().strftime('%Y-%m-%d')
    today_dow = datetime.now().weekday()
    
    chores = []
    for chore in data.get('chores', []):
        schedule = chore.get('schedule', 'weekly')
        last_done = chore.get('last_done', '')
        
        should_show = False
        
        if schedule == 'daily':
            should_show = True
        elif schedule == 'weekly':
            if today_dow == 0:  # Sunday
                should_show = True
        elif schedule == 'biweekly':
            if today_dow == 0:
                if last_done:
                    try:
                        last = datetime.strptime(last_done, '%Y-%m-%d')
                        if (datetime.now() - last).days >= 14:
                            should_show = True
                    except:
                        should_show = True
                else:
                    should_show = True
        elif schedule == 'monthly':
            if today_dow == 0 and datetime.now().day <= 7:
                if last_done:
                    try:
                        last = datetime.strptime(last_done, '%Y-%m-%d')
                        if (datetime.now() - last).days >= 30:
                            should_show = True
                    except:
                        should_show = True
                else:
                    should_show = True
        
        if should_show:
            chores.append(chore['name'])
    
    return chores

@app.route('/')
def index():
    return render_template('index.html', weather_city=WEATHER_CITY)

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

@app.route('/chores')
def chores():
    return {'chores': get_today_chores()}

@app.route('/telemetry', methods=['GET', 'POST'])
def telemetry():
    data = load_data()
    
    if request.method == 'POST':
        entry = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'metrics': request.json.get('metrics', {})
        }
        data['telemetry'].append(entry)
        save_data(data)
        return jsonify({'success': True})
    
    return render_template('telemetry.html', entries=data.get('telemetry', []))

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
