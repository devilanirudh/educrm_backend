#!/bin/bash

# E-School Management Platform - Backend Startup Script
# Run this script from the backend directory

echo "🏫 E-School Management Platform - Backend"
echo "========================================"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment: $VIRTUAL_ENV"
else
    echo "⚠️  Warning: No virtual environment detected"
    echo "💡 Recommendation: Activate your virtual environment first"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate  # On Mac/Linux"
    echo "   venv\\Scripts\\activate     # On Windows"
    echo
fi

# Check if requirements are installed
echo "🔍 Checking dependencies..."
if python -c "import fastapi, uvicorn, duckdb" 2>/dev/null; then
    echo "✅ Core dependencies found"
else
    echo "❌ Missing dependencies. Installing..."
    pip install -r requirements.txt
fi

echo
echo "🚀 Starting FastAPI server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "📖 ReDoc Documentation: http://localhost:8000/redoc"
echo
echo "Press Ctrl+C to stop the server"
echo "========================================"

# Start the server
python run_server.py
