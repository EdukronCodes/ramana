#!/bin/bash

# Quick Start Script with Testing

echo "🚀 PDF Processor MCP Server - Quick Start"
echo "=========================================="
echo ""

# Check Python version
python3 --version

# Install dependencies if needed
if [ ! -f "venv/bin/activate" ]; then
    echo "📦 Setting up virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check for .env
if [ ! -f ".env" ]; then
    echo "⚠️  Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your GOOGLE_API_KEY"
    echo "   Get your key from: https://makersuite.google.com/app/apikey"
    echo ""
    read -p "Press Enter after you've added your API key..."
fi

# Create directories
mkdir -p data/uploads data/vectorstore

echo ""
echo "✅ Setup complete!"
echo ""
echo "Choose an option:"
echo "  1) Start Web Server (Recommended)"
echo "  2) Start MCP Server"
echo "  3) Run Tests"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🌐 Starting Web Server..."
        echo "📍 Open http://localhost:8000 in your browser"
        echo ""
        python web_server.py
        ;;
    2)
        echo ""
        echo "🔧 Starting MCP Server..."
        python server.py
        ;;
    3)
        echo ""
        echo "🧪 Running tests..."
        echo "⚠️  Make sure the web server is running in another terminal!"
        echo ""
        python test_server.py
        ;;
    *)
        echo "Invalid choice"
        ;;
esac
