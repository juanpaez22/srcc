from flask import Flask, render_template_string
import psutil
import time

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Stone Ranch Command Center</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .container {
            text-align: center;
            background: #16213e;
            padding: 40px 60px;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        h1 {
            margin: 0 0 30px 0;
            font-size: 28px;
            color: #e94560;
        }
        .stat {
            margin: 20px 0;
            font-size: 18px;
        }
        .value {
            font-size: 48px;
            font-weight: bold;
            color: #0f3460;
            background: #eee;
            padding: 10px 20px;
            border-radius: 8px;
            display: inline-block;
            min-width: 120px;
        }
        .label {
            display: block;
            font-size: 14px;
            color: #888;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .updated {
            margin-top: 30px;
            font-size: 12px;
            color: #555;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Stone Ranch Command Center</h1>
        
        <div class="stat">
            <span class="label">CPU Usage</span>
            <div class="value" id="cpu">{{ cpu }}%</div>
        </div>
        
        <div class="stat">
            <span class="label">Memory Usage</span>
            <div class="value" id="mem">{{ memory }}%</div>
        </div>
        
        <div class="updated">
            Last updated: <span id="time">{{ time }}</span>
        </div>
    </div>

    <script>
        function updateStats() {
            fetch('/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('cpu').textContent = data.cpu + '%';
                    document.getElementById('mem').textContent = data.memory + '%';
                    document.getElementById('time').textContent = data.time;
                });
        }
        
        updateStats();
        setInterval(updateStats, 2000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE, cpu=0, memory=0, time='--')

@app.route('/stats')
def stats():
    return {
        'cpu': psutil.cpu_percent(),
        'memory': psutil.virtual_memory().percent,
        'time': time.strftime('%H:%M:%S')
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
