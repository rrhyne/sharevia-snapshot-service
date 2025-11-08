#!/bin/bash
# Snapshot Service Manager
# Quick script to start/stop/status the snapshot service

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/snapshot-service.pid"
LOG_FILE="$SCRIPT_DIR/logs/snapshot.log"
SERVICE_SCRIPT="$SCRIPT_DIR/main.py"

case "$1" in
    start)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "❌ Service is already running (PID: $(cat "$PID_FILE"))"
            exit 1
        fi
        
        echo "🚀 Starting snapshot service..."
        mkdir -p logs
        cd "$SCRIPT_DIR"
        nohup python3 "$SERVICE_SCRIPT" > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo "✅ Service started (PID: $(cat "$PID_FILE"))"
        echo "📝 Logs: tail -f $LOG_FILE"
        ;;
        
    stop)
        if [ ! -f "$PID_FILE" ]; then
            echo "❌ Service is not running"
            exit 1
        fi
        
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "🛑 Stopping snapshot service (PID: $PID)..."
            kill "$PID"
            rm "$PID_FILE"
            echo "✅ Service stopped"
        else
            echo "❌ Service is not running (stale PID file)"
            rm "$PID_FILE"
        fi
        ;;
        
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
        
    status)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            PID=$(cat "$PID_FILE")
            echo "✅ Service is running (PID: $PID)"
            echo "📊 Process info:"
            ps -p "$PID" -o pid,ppid,%cpu,%mem,etime,command
        else
            echo "❌ Service is not running"
            [ -f "$PID_FILE" ] && rm "$PID_FILE"
            exit 1
        fi
        ;;
        
    logs)
        if [ ! -f "$LOG_FILE" ]; then
            echo "❌ No log file found"
            exit 1
        fi
        tail -f "$LOG_FILE"
        ;;
        
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the snapshot service"
        echo "  stop     - Stop the snapshot service"
        echo "  restart  - Restart the snapshot service"
        echo "  status   - Check service status"
        echo "  logs     - Tail the log file"
        exit 1
        ;;
esac

exit 0
