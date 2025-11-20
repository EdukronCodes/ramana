"""
Web API Server for PDF Processor
FastAPI server to provide HTTP interface to MCP server
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import shutil
import uvicorn
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

from src.pdf_processor import pdf_processor
from src.agents import pdf_agents
from src.config import UPLOAD_DIR

app = FastAPI(title="PDF Processor API", version="1.0.0")

# Thread pool for background tasks
executor = ThreadPoolExecutor(max_workers=4)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and send status updates
            await asyncio.sleep(0.5)
            
            # Check processing status for all documents
            status_updates = {}
            for doc_id in pdf_processor.metadata.keys():
                status = pdf_processor.get_processing_status(doc_id)
                if status:
                    status_updates[doc_id] = status
            
            if status_updates:
                await websocket.send_json({
                    "type": "status_update",
                    "data": status_updates
                })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


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
async def process_pdf(request: ProcessRequest, background_tasks: BackgroundTasks):
    """Process an uploaded PDF in background."""
    try:
        # Check if document exists
        if request.document_id not in pdf_processor.metadata:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Start processing in background
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor, 
            pdf_processor.process_pdf, 
            request.document_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        # Broadcast completion
        await manager.broadcast({
            "type": "processing_complete",
            "document_id": request.document_id,
            "result": result
        })
        
        return result

    except HTTPException:
        raise
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


@app.get("/api/status/{document_id}")
async def get_processing_status(document_id: str):
    """Get current processing status for a document."""
    try:
        status = pdf_processor.get_processing_status(document_id)
        if status:
            return {"success": True, "status": status}
        else:
            # Check if document is already processed
            if document_id in pdf_processor.metadata:
                doc = pdf_processor.metadata[document_id]
                if doc.get("processed"):
                    return {"success": True, "status": {"stage": "completed", "progress": 100, "total": 100}}
            return {"success": True, "status": None}
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
