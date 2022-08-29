#!/bin/bash
/usr/bin/inotifywait -q -m -r -e CLOSE_WRITE --exclude '\.git' --format="(cd /home/nathanahn/sync-docs ; git add -A && git commit -m 'Auto Commit' && git push)" /home/nathanahn/sync-docs | /usr/bin/bash
