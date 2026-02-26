#!/bin/bash
cd /home/juanpaez/dev/nanobot 
echo "Current HEAD: $(git log --oneline -1)"
echo "v0.1.4.post2: $(git rev-parse v0.1.4.post2)"
echo "Behind? $(git rev-list --count HEAD..v0.1.4.post2) commits"
