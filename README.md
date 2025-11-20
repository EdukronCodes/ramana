# PDF Processor MCP Server

An advanced Model Context Protocol (MCP) server for processing large PDFs (up to 500 pages) using LangChain multi-agent system and Google Gemini AI.

## Features

- 📄 **PDF Processing**: Upload and process PDFs up to 500 pages
- 🤖 **Multi-Agent System**: Specialized agents for different tasks:
  - **Coordinator Agent**: Routes tasks to appropriate agents
  - **Summarizer Agent**: Generates brief, detailed, or executive summaries
  - **Q&A Agent**: Answers questions about document content
  - **Extraction Agent**: Extracts key points, statistics, references, etc.
- 🧠 **Gemini AI Integration**: Powered by Google's Gemini 1.5 Pro
- 🔍 **Vector Search**: ChromaDB for semantic document search
- 🌐 **Web UI**: Modern, responsive web interface
- 📡 **MCP Server**: Full Model Context Protocol implementation
- 🔌 **REST API**: FastAPI-based HTTP interface

## Architecture

```
┌─────────────────┐
│   Web UI        │
│  (HTML/CSS/JS)  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  FastAPI Server │
│  (web_server.py)│
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────────┐
│      MCP Server Core                │
│  ┌──────────────────────────────┐  │
│  │  PDF Processor               │  │
│  │  - Text extraction           │  │
│  │  - Chunking                  │  │
│  │  - Vector store creation     │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │  Multi-Agent System          │  │
│  │  - Coordinator Agent         │  │
│  │  - Summarizer Agent          │  │
│  │  - Q&A Agent                 │  │
│  │  - Extraction Agent          │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
         │
         ↓
┌─────────────────┐
│   Gemini AI     │
│  Google API     │
└─────────────────┘
```

## Installation

### Prerequisites

- Python 3.10 or higher
- Google Gemini API key

### Setup

1. **Clone the repository**:
   ```bash
   cd /workspaces/ramana
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   ```

5. **Edit `.env` file**:
   ```bash
   # Add your Google Gemini API key
   GOOGLE_API_KEY=your_api_key_here
   ```

   Get your API key from: https://makersuite.google.com/app/apikey

## Usage

### Running the Web Server

Start the FastAPI web server with UI:

```bash
python web_server.py
```

Then open your browser to: http://localhost:8000

### Running the MCP Server

To run as a standalone MCP server:

```bash
python server.py
```

## Web UI Guide

### 1. Upload PDF
- Select a PDF file (max 500 pages)
- Enter a document ID or let it auto-generate
- Click "Upload & Process"
- Wait for processing to complete

### 2. Ask Questions
- Select a processed document
- Type your question
- Get AI-powered answers with source citations

### 3. Generate Summary
- Select a document
- Choose summary type:
  - **Brief**: 2-3 paragraphs
  - **Detailed**: Comprehensive overview
  - **Executive**: Business-focused summary
- Generate summary

### 4. Extract Information
- Select a document
- Choose extraction type:
  - Key Points
  - Statistics & Numbers
  - References & Citations
  - Definitions & Terms
  - Action Items

## API Endpoints

### Upload PDF
```http
POST /api/upload
Content-Type: multipart/form-data

file: <pdf file>
document_id: <string>
```

### Process PDF
```http
POST /api/process
Content-Type: application/json

{
  "document_id": "doc-001"
}
```

### Query Document
```http
POST /api/query
Content-Type: application/json

{
  "document_id": "doc-001",
  "query": "What are the main findings?"
}
```

### Generate Summary
```http
POST /api/summarize
Content-Type: application/json

{
  "document_id": "doc-001",
  "summary_type": "detailed"
}
```

### Extract Information
```http
POST /api/extract
Content-Type: multipart/form-data

document_id: <string>
extraction_type: <string>
```

### List Documents
```http
GET /api/documents
```

## MCP Tools

The MCP server provides the following tools:

1. **upload_pdf**: Upload a PDF file for processing
2. **process_pdf**: Process an uploaded PDF with multi-agent analysis
3. **query_pdf**: Ask questions about a processed PDF
4. **summarize_pdf**: Generate a comprehensive summary
5. **list_pdfs**: List all uploaded and processed PDFs

## Configuration

Edit `.env` file to customize:

```env
# Google Gemini API Key
GOOGLE_API_KEY=your_api_key_here

# Server Configuration
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000

# PDF Processing
MAX_PDF_PAGES=500
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Vector Store
VECTOR_STORE_PATH=./data/vectorstore
```

## Project Structure

```
ramana/
├── src/
│   ├── __init__.py          # MCP server initialization
│   ├── config.py            # Configuration settings
│   ├── handlers.py          # MCP tool handlers
│   ├── pdf_processor.py     # PDF processing logic
│   └── agents.py            # LangChain multi-agent system
├── web/
│   ├── index.html           # Web UI
│   └── static/
│       ├── style.css        # UI styles
│       └── app.js           # UI JavaScript
├── data/
│   ├── uploads/             # Uploaded PDFs
│   └── vectorstore/         # Vector embeddings
├── server.py                # MCP server entry point
├── web_server.py            # FastAPI web server
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Project configuration
├── .env.example            # Environment template
└── README.md               # This file
```

## Multi-Agent System

### Coordinator Agent
Routes tasks to specialized agents based on the request type.

### Summarizer Agent
Generates three types of summaries:
- **Brief**: Quick overview
- **Detailed**: Comprehensive analysis
- **Executive**: Business-focused insights

### Q&A Agent
Answers questions using:
- Retrieval-Augmented Generation (RAG)
- Vector similarity search
- Source document citations

### Extraction Agent
Extracts specific information:
- Key points and takeaways
- Statistics and numerical data
- References and citations
- Definitions and terminology
- Action items and recommendations

## Technologies Used

- **MCP**: Model Context Protocol for tool integration
- **LangChain**: Agent orchestration and chain management
- **Google Gemini**: Large language model (Gemini 1.5 Pro)
- **ChromaDB**: Vector database for semantic search
- **PyPDF2**: PDF text extraction
- **FastAPI**: Web API framework
- **Uvicorn**: ASGI server

## Troubleshooting

### API Key Error
```
ValueError: GOOGLE_API_KEY not found in environment variables
```
**Solution**: Ensure `.env` file exists and contains valid API key.

### PDF Too Large
```
PDF has X pages, exceeds maximum of 500
```
**Solution**: Split PDF into smaller documents or increase `MAX_PDF_PAGES` in `.env`.

### Vector Store Error
```
Error creating vector store
```
**Solution**: Check write permissions for `data/vectorstore/` directory.

### Import Errors
```
ModuleNotFoundError: No module named 'X'
```
**Solution**: Install dependencies: `pip install -r requirements.txt`

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/ web_server.py server.py
```

### Linting
```bash
ruff check src/ web_server.py server.py
```

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- Open an issue on GitHub
- Check documentation at `/docs`

## Acknowledgments

- Google Gemini AI
- LangChain community
- MCP protocol developers
