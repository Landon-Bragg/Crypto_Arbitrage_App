#!/bin/bash

echo "Setting up Crypto Arbitrage App..."

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

# Install Python dependencies
echo "Installing Python dependencies..."
cd python_backend
python -m pip install -r ../requirements.txt
cd ..

echo "Setup complete!"
echo ""
echo "To run the application:"
echo "1. Start the Python backend: cd python_backend && python server.py"
echo "2. Start the Next.js frontend: npm run dev"
echo "3. Open http://localhost:3000 in your browser"