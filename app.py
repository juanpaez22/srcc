from flask import Flask, render_template
import psutil
import time
import requests

app = Flask(__name__)

KIRKLAND_LAT = 47.6769
KIRKLAND_LON = -122.2060

def get_weather():
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={KIRKLAND_LAT}&longitude={KIRKLAND_LON}&current=temperature_2m,weather_code,wind_speed_10m"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        current = data.get('current', {})
        
        temp_f = round(current.get('temperature_2m', 0) * 9/5 + 32)
        wind = current.get('wind_speed_10m', 0)
        code = current.get('weather_code', 0)
        
        conditions = {
            0: "Clear",
            1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
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
            'error': None
        }
    except Exception as e:
        return {'temp': '--', 'condition': '--', 'wind': '--', 'error': str(e)}

@app.route('/')
def index():
    return render_template('index.html')

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
