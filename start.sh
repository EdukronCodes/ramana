#!/bin/bash

# PDF Processor MCP Server - Start Script

echo "🚀 Starting PDF Processor MCP Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your GOOGLE_API_KEY"
    echo "   Get your key from: https://makersuite.google.com/app/apikey"
    exit 1
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/uploads
mkdir -p data/vectorstore

# Start the web server
echo "🌐 Starting web server on http://localhost:8000"
echo "✨ Open your browser to http://localhost:8000"
echo ""
python web_server.py
