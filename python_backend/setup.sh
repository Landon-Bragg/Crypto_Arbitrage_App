#!/bin/bash

echo "🔧 Setting up Python backend for live market data..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📥 Installing Python dependencies..."
pip install -r ../requirements.txt

# Copy environment file
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys (optional for public data)"
fi

echo "✅ Setup complete!"
echo ""
echo "To test the live data:"
echo "1. python test_live_data.py"
echo ""
echo "To start the API server:"
echo "1. python server.py"
echo "2. Visit http://localhost:8000/docs for API documentation"
