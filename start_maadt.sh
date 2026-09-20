#!/bin/bash
echo "Starting MAADT System..."

# Start Python Backend
cd backend
source venv/bin/activate
python api/main.py &
BACKEND_PID=$!
echo "Backend started at PID $BACKEND_PID"

# Start Next.js Frontend
cd ../frontend
npm run dev &
FRONTEND_PID=$!
echo "Frontend started at PID $FRONTEND_PID"

echo "System is running. Open http://localhost:3000 in your browser."
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
