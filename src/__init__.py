"""
PDF Processor MCP Server
A Model Context Protocol server for processing large PDFs using LangChain multi-agents and Gemini AI
"""

import os
from typing import Any, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("pdf-processor-mcp")

# Import handlers after server initialization
from .handlers import (
    handle_upload_pdf,
    handle_process_pdf,
    handle_query_pdf,
    handle_summarize_pdf,
    handle_list_pdfs,
)

# Register tools
@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="upload_pdf",
            description="Upload a PDF file for processing (max 500 pages)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the PDF file to upload",
                    },
                    "document_id": {
                        "type": "string",
                        "description": "Unique identifier for the document",
                    },
                },
                "required": ["file_path", "document_id"],
            },
        ),
        Tool(
            name="process_pdf",
            description="Process an uploaded PDF with multi-agent analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "Document ID to process",
                    },
                },
                "required": ["document_id"],
            },
        ),
        Tool(
            name="query_pdf",
            description="Ask questions about a processed PDF",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "Document ID to query",
                    },
                    "query": {
                        "type": "string",
                        "description": "Question to ask about the document",
                    },
                },
                "required": ["document_id", "query"],
            },
        ),
        Tool(
            name="summarize_pdf",
            description="Generate a comprehensive summary of a PDF",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "Document ID to summarize",
                    },
                    "summary_type": {
                        "type": "string",
                        "enum": ["brief", "detailed", "executive"],
                        "description": "Type of summary to generate",
                    },
                },
                "required": ["document_id"],
            },
        ),
        Tool(
            name="list_pdfs",
            description="List all uploaded and processed PDFs",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "upload_pdf":
            result = await handle_upload_pdf(arguments)
        elif name == "process_pdf":
            result = await handle_process_pdf(arguments)
        elif name == "query_pdf":
            result = await handle_query_pdf(arguments)
        elif name == "summarize_pdf":
            result = await handle_summarize_pdf(arguments)
        elif name == "list_pdfs":
            result = await handle_list_pdfs(arguments)
        else:
            result = f"Unknown tool: {name}"

        return [TextContent(type="text", text=str(result))]
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())
