#!/bin/bash

echo "🚀 Setting up Professional Crypto Arbitrage Platform..."

# Install Node.js dependencies
echo "📦 Installing frontend dependencies..."
npm install

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
cd python_backend
python -m pip install -r ../requirements.txt
cd ..

echo "✅ Setup complete!"
echo ""
echo "🚀 To run the application:"
echo "1. Backend:  cd python_backend && python server.py"
echo "2. Frontend: npm run dev"
echo "3. Open:     http://localhost:3000"
echo ""
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check:      http://localhost:8000/health"
