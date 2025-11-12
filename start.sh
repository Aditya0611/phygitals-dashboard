#!/bin/sh
set -e

echo "[start.sh] Bootstrapping application at $(date -Is)"

# Start the scheduler in the background so it can trigger scrapes
node /app/scheduler.js &

# Launch the Next.js server in the foreground
exec npm start
