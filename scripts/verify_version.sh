#!/bin/bash
cd /home/juanpaez/dev/nanobot 
echo "HEAD: $(git rev-parse HEAD)"
echo "v0.1.4.post2: $(git rev-parse v0.1.4.post2)"
git log --oneline v0.1.4.post2 -3
