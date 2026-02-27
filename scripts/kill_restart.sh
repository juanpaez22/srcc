#!/bin/bash
# Kill old process
ps aux | grep "python app.py" | grep -v grep | awk '{print $2}' | xargs -r sudo kill
sleep 1
# Start new
cd /home/juanpaez/.nanobot/workspace/dev/srcc
sudo python app.py > /tmp/srcc.log 2>&1 &
