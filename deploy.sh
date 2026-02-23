#!/bin/bash
# Stone Ranch Command Center - Deploy Script

cd ~/dev/srcc || exit 1

echo "Pulling latest from GitHub..."
git pull origin master || { echo "Git pull failed"; exit 1; }

echo "Killing existing server..."
sudo pkill -f "python3.*app.py" 2>/dev/null
sleep 2

echo "Starting server..."
cd ~/dev/srcc
chmod +x deploy.sh
nohup sudo python3 app.py > app.log 2>&1 &
sleep 3

if pgrep -f "python3.*app.py" > /dev/null; then
    echo "Server started successfully!"
    curl -s localhost/weather | head -5
else
    echo "Server failed to start. Check app.log"
    cat app.log
fi
