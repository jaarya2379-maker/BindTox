#!/bin/bash
# BindTox Complete Application Startup Script
# Starts both backend API and Streamlit UI with proper environment configuration

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Detect the Miniforge conda environment
CONDA_ENV_DIR="/opt/homebrew/Caskroom/miniforge/base/envs/bindtox-py310"

# Check if conda environment exists
if [ ! -d "$CONDA_ENV_DIR" ]; then
    echo "❌ Error: Conda environment not found at $CONDA_ENV_DIR"
    echo "Please ensure the bindtox-py310 conda environment is installed."
    exit 1
fi

# Set Python and environment variables
export PYTHONPATH="$SCRIPT_DIR/src"
export CONDA_PREFIX="$CONDA_ENV_DIR"
PYTHON="$CONDA_ENV_DIR/bin/python"
STREAMLIT="$CONDA_ENV_DIR/bin/streamlit"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    killall python 2>/dev/null || true
    sleep 1
    echo "✓ All services stopped"
}

# Set trap to cleanup on exit
trap cleanup EXIT INT TERM

# Check if ports are available
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Error: Port $port is already in use (by $service)"
        echo "Please stop the other application or use different ports."
        exit 1
    fi
}

check_port 8000 "Backend"
check_port 8501 "Streamlit"

echo "🚀 Starting BindTox Complete..."
echo ""

# Start backend API
echo "📡 Starting Backend API on http://0.0.0.0:8000"
$PYTHON -m bindtox.cli serve-api --host 0.0.0.0 --port 8000 > /tmp/bindtox_backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Wait for backend to start
sleep 3

# Check if backend is running
if ! ps -p $BACKEND_PID > /dev/null; then
    echo "❌ Backend failed to start. Checking logs..."
    tail -20 /tmp/bindtox_backend.log
    exit 1
fi

# Health check
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  Backend health check failed. Waiting a bit more..."
    sleep 3
fi

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Backend is responding"
else
    echo "⚠️  Backend may not be responding. Check logs with: tail -f /tmp/bindtox_backend.log"
fi

echo ""

# Start Streamlit UI
echo "🎨 Starting Streamlit UI on http://0.0.0.0:8501"
$STREAMLIT run streamlit_app.py --server.address 0.0.0.0 --server.port 8501 > /tmp/bindtox_streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo "   Streamlit PID: $STREAMLIT_PID"

# Wait for Streamlit to start
sleep 5

# Check if Streamlit is running
if ! ps -p $STREAMLIT_PID > /dev/null; then
    echo "❌ Streamlit failed to start. Checking logs..."
    tail -20 /tmp/bindtox_streamlit.log
    exit 1
fi

echo "✓ Streamlit is running"

echo ""
echo "✅ BindTox Complete is ready!"
echo ""
echo "📍 Access the application:"
echo "   Local:   http://localhost:8501"
echo "   Network: http://$(hostname -I | awk '{print $1}'):8501"
echo ""
echo "📊 Backend API:"
echo "   Health: http://localhost:8000/health"
echo "   Docs:   http://localhost:8000/docs"
echo ""
echo "📋 Logs:"
echo "   Backend:   tail -f /tmp/bindtox_backend.log"
echo "   Streamlit: tail -f /tmp/bindtox_streamlit.log"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

# Keep the script running
wait $BACKEND_PID $STREAMLIT_PID 2>/dev/null || true
