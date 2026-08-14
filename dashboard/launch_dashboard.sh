#!/usr/bin/env bash
# StrokeGuard dashboard launcher (runs on HOST, arduino user, on DISPLAY=:0)
# Starts the dashboard web server and opens the beautiful kiosk window
# on the connected monitor (LG via Type-C dock).

set -e

# --- config ---
PORT="${STROKEGUARD_PORT:-8091}"
DISPLAY="${STROKEGUARD_DISPLAY:-:0}"
DASH_DIR="$HOME/strokeguard_dashboard"
LOG_DIR="$HOME/.strokeguard"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/dashboard.log"

# --- start web server (idempotent) ---
if ! curl -sf "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; then
    nohup python3 "$DASH_DIR/dashboard_server.py" --port "$PORT" \
        >> "$LOG_FILE" 2>&1 &
    echo "dashboard server started on :$PORT" >> "$LOG_FILE"
    sleep 1
fi

# --- open kiosk on the external monitor ---
# export X authority + display for the arduino session on :0
export DISPLAY="$DISPLAY"
export XAUTHORITY="$HOME/.Xauthority"

# kill any existing kiosk to avoid stacking windows
pkill -f "chromium.*strokeguard_dashboard" 2>/dev/null || true
sleep 1

# launch kiosk (only one window, no UI clutter)
chromium-browser \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --kiosk \
    --window-position=0,0 \
    --window-size=1920,1080 \
    --autoplay-policy=no-user-gesture-required \
    "http://127.0.0.1:$PORT/" \
    >> "$LOG_FILE" 2>&1 &

echo "kiosk launched on $DISPLAY at $(date)" >> "$LOG_FILE"