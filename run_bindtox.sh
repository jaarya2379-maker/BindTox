#!/bin/bash
set -euo pipefail

###############################################################################
# BindTox Reliable Startup Script
# ═════════════════════════════════════════════════════════════════════════
# This script starts BindTox backend and UI reliably on any network.
# It handles:
#   - Python environment activation
#   - Package installation
#   - Port conflicts
#   - Network binding (0.0.0.0 for all interfaces)
#   - Error handling and logging
###############################################################################

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_BIN="/opt/homebrew/Caskroom/miniforge/base/envs/bindtox-py310/bin/python"
LOG_DIR="/tmp/bindtox_logs"
BACKEND_PORT="${BACKEND_PORT:-8000}"
UI_PORT="${UI_PORT:-8501}"
NETWORK_HOST="${NETWORK_HOST:-0.0.0.0}"

###############################################################################
# Functions
###############################################################################

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    echo "[ERROR] $*" >&2
    exit 1
}

cleanup() {
    log "Cleaning up processes..."
    pkill -f "uvicorn.*bindtox.backend_api" || true
    pkill -f "streamlit.*streamlit_app.py" || true
    sleep 1
}

check_python() {
    if [ ! -x "$PYTHON_BIN" ]; then
        error "Python not found at: $PYTHON_BIN"
    fi
    log "Python: $($PYTHON_BIN --version)"
}

check_ports() {
    local port=$1
    if lsof -Pi ":$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
        log "Killing process on port $port..."
        lsof -ti ":$port" | xargs kill -9 || true
        sleep 1
    fi
}

install_package() {
    log "Installing bindtox package..."
    cd "$PROJECT_DIR"
    "$PYTHON_BIN" -m pip install -e . -q 2>&1 | grep -i "successfully\|error" || true
    log "Package installation completed"
}

verify_imports() {
    log "Verifying bindtox imports..."
    "$PYTHON_BIN" -c "
from bindtox.chemistry import calculate_properties
from bindtox.backend_api import app
from bindtox.cli import main
print('✅ All imports successful')
" || error "Import verification failed"
}

start_backend() {
    log "Starting backend on $NETWORK_HOST:$BACKEND_PORT..."
    mkdir -p "$LOG_DIR"
    
    nohup "$PYTHON_BIN" -m bindtox.cli serve-api \
        --host "$NETWORK_HOST" \
        --port "$BACKEND_PORT" \
        > "$LOG_DIR/backend.log" 2>&1 &
    
    BACKEND_PID=$!
    log "Backend PID: $BACKEND_PID"
    
    # Wait for backend to be ready
    sleep 3
    
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null 2>&1; then
            log "✅ Backend is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    error "Backend failed to start after ${max_attempts}s. Check: $LOG_DIR/backend.log"
}

start_ui() {
    log "Starting Streamlit UI on $NETWORK_HOST:$UI_PORT..."
    
    nohup "$PYTHON_BIN" -m streamlit run streamlit_app.py \
        --server.address "$NETWORK_HOST" \
        --server.port "$UI_PORT" \
        --logger.level=error \
        > "$LOG_DIR/ui.log" 2>&1 &
    
    UI_PID=$!
    log "UI PID: $UI_PID"
    
    # Wait for UI to be ready
    sleep 4
    
    if curl -I -s "http://127.0.0.1:$UI_PORT" >/dev/null 2>&1; then
        log "✅ UI is ready"
        return 0
    else
        log "⚠️  UI may still be starting, check logs at: $LOG_DIR/ui.log"
    fi
}

get_network_ip() {
    # Get the primary network interface IP
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "127.0.0.1"
    else
        # Linux
        hostname -I | awk '{print $1}' || echo "127.0.0.1"
    fi
}

###############################################################################
# Main
###############################################################################

main() {
    log "════════════════════════════════════════════════════════════════════"
    log "           BindTox Startup (Reliable & Network-Ready)"
    log "════════════════════════════════════════════════════════════════════"
    log ""
    
    # Cleanup old processes
    cleanup
    
    # Verify environment
    check_python
    check_ports "$BACKEND_PORT"
    check_ports "$UI_PORT"
    
    # Install and verify package
    install_package
    verify_imports
    
    log ""
    log "Starting services..."
    log ""
    
    # Start services
    start_backend
    start_ui
    
    # Print access information
    local network_ip=$(get_network_ip)
    
    log ""
    log "════════════════════════════════════════════════════════════════════"
    log "✅ BindTox is running!"
    log "════════════════════════════════════════════════════════════════════"
    log ""
    log "📡 ACCESS URLS:"
    log ""
    log "   Local:        http://localhost:$UI_PORT"
    log "   Network (LAN): http://$network_ip:$UI_PORT"
    log "   API Docs:     http://localhost:$BACKEND_PORT/docs"
    log ""
    log "📝 LOGS:"
    log "   Backend: $LOG_DIR/backend.log"
    log "   UI:      $LOG_DIR/ui.log"
    log ""
    log "🛑 TO STOP:"
    log "   Press Ctrl+C or run: pkill -f bindtox"
    log ""
    log "════════════════════════════════════════════════════════════════════"
    log ""
    
    # Keep script running
    wait
}

main "$@"
