"""
Web API Server for PDF Processor
FastAPI server to provide HTTP interface to MCP server
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import shutil
import uvicorn

from src.pdf_processor import pdf_processor
from src.agents import pdf_agents
from src.config import UPLOAD_DIR

app = FastAPI(title="PDF Processor API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")


# Request/Response models
class QueryRequest(BaseModel):
    document_id: str
    query: str


class SummaryRequest(BaseModel):
    document_id: str
    summary_type: Optional[str] = "detailed"


class ProcessRequest(BaseModel):
    document_id: str


# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main UI."""
    return FileResponse("web/index.html")


@app.post("/api/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    document_id: str = Form(...)
):
    """Upload a PDF file."""
    try:
        # Save uploaded file
        file_path = UPLOAD_DIR / f"{document_id}.pdf"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process upload
        result = pdf_processor.upload_pdf(str(file_path), document_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process")
async def process_pdf(request: ProcessRequest):
    """Process an uploaded PDF."""
    try:
        result = pdf_processor.process_pdf(request.document_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query")
async def query_pdf(request: QueryRequest):
    """Query a processed PDF."""
    try:
        result = await pdf_agents.qa_agent(request.document_id, request.query)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/summarize")
async def summarize_pdf(request: SummaryRequest):
    """Generate a summary of a PDF."""
    try:
        result = await pdf_agents.summarizer_agent(
            request.document_id, 
            request.summary_type
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents")
async def list_documents():
    """List all uploaded documents."""
    try:
        documents = pdf_processor.list_documents()
        return {"success": True, "documents": documents}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/document/{document_id}")
async def get_document_info(document_id: str):
    """Get information about a specific document."""
    try:
        documents = pdf_processor.list_documents()
        doc = next((d for d in documents if d["document_id"] == document_id), None)
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"success": True, "document": doc}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/extract")
async def extract_info(document_id: str = Form(...), extraction_type: str = Form(...)):
    """Extract specific information from a PDF."""
    try:
        result = await pdf_agents.extraction_agent(document_id, extraction_type)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
