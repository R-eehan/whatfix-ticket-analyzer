#!/bin/bash

# Start the backend and frontend for Whatfix Ticket Analyzer

echo "Starting Whatfix Ticket Analyzer..."
echo "=================================="

# Check if GOOGLE_API_KEY is set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "Warning: GOOGLE_API_KEY is not set in environment"
    echo "The system will use the default configuration if available"
    echo ""
fi

# Function to kill processes on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup EXIT

# Start backend
echo "Starting backend server..."
cd backend
python -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend
echo "Starting frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "=================================="
echo "Servers started successfully!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "=================================="

# Wait for user to press Ctrl+C
wait
