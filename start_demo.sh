#!/bin/bash
echo "🚀 Starting Job Orchestration Platform Demo"
echo ""

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "❌ Backend is not running. Start it with:"
    echo "   cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000"
    exit 1
fi

# Start frontend
echo "🌐 Starting frontend..."
cd frontend
npm run dev > /dev/null 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend starting on http://localhost:3000 (PID: $FRONTEND_PID)"
echo ""
echo "📊 Demo URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
wait $FRONTEND_PID
