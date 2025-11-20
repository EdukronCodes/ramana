"""
Configuration settings for PDF Processor MCP Server
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# Server Configuration
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "localhost")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8000"))

# PDF Processing Configuration
MAX_PDF_PAGES = int(os.getenv("MAX_PDF_PAGES", "500"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# Storage Configuration
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", str(DATA_DIR / "vectorstore"))

# Create necessary directories
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
Path(VECTOR_STORE_PATH).parent.mkdir(parents=True, exist_ok=True)

# Gemini Model Configuration
GEMINI_MODEL = "gemini-1.5-pro"
GEMINI_TEMPERATURE = 0.7
GEMINI_MAX_TOKENS = 8192
