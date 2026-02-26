#!/bin/bash
cd /home/juanpaez/.nanobot/workspace/dev/srcc
git add app.py
git commit -m "$1"
git push
