#!/bin/bash

# Development startup script

set -e

echo "🚀 Starting FreeSWITCH CTI in development mode"

# Function to cleanup background processes
cleanup() {
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Trap cleanup on script exit
trap cleanup EXIT INT TERM

# Start backend
echo "📡 Starting backend server..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "🖥️ Starting frontend application..."
cd frontend
npm run dev &
FRONTEND_PID=$!

cd ..

echo "✅ Services started!"
echo "Backend: http://localhost:8000"
echo "Frontend: Electron app should open automatically"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for background processes
wait