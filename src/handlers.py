"""
MCP Tool Handlers
Implements handlers for each MCP tool
"""

import logging
from typing import Any, Dict
from .pdf_processor import pdf_processor
from .agents import pdf_agents

logger = logging.getLogger(__name__)


async def handle_upload_pdf(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle PDF upload tool.
    
    Args:
        arguments: Dictionary with file_path and document_id
        
    Returns:
        Upload result dictionary
    """
    try:
        file_path = arguments.get("file_path")
        document_id = arguments.get("document_id")

        if not file_path or not document_id:
            return {"success": False, "error": "Missing required arguments"}

        result = pdf_processor.upload_pdf(file_path, document_id)
        return result

    except Exception as e:
        logger.error(f"Error in upload_pdf handler: {str(e)}")
        return {"success": False, "error": str(e)}


async def handle_process_pdf(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle PDF processing tool.
    
    Args:
        arguments: Dictionary with document_id
        
    Returns:
        Processing result dictionary
    """
    try:
        document_id = arguments.get("document_id")

        if not document_id:
            return {"success": False, "error": "Missing document_id"}

        result = pdf_processor.process_pdf(document_id)
        return result

    except Exception as e:
        logger.error(f"Error in process_pdf handler: {str(e)}")
        return {"success": False, "error": str(e)}


async def handle_query_pdf(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle PDF query tool.
    
    Args:
        arguments: Dictionary with document_id and query
        
    Returns:
        Query result dictionary
    """
    try:
        document_id = arguments.get("document_id")
        query = arguments.get("query")

        if not document_id or not query:
            return {"success": False, "error": "Missing required arguments"}

        result = await pdf_agents.qa_agent(document_id, query)
        return result

    except Exception as e:
        logger.error(f"Error in query_pdf handler: {str(e)}")
        return {"success": False, "error": str(e)}


async def handle_summarize_pdf(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle PDF summarization tool.
    
    Args:
        arguments: Dictionary with document_id and optional summary_type
        
    Returns:
        Summary result dictionary
    """
    try:
        document_id = arguments.get("document_id")
        summary_type = arguments.get("summary_type", "detailed")

        if not document_id:
            return {"success": False, "error": "Missing document_id"}

        result = await pdf_agents.summarizer_agent(document_id, summary_type)
        return result

    except Exception as e:
        logger.error(f"Error in summarize_pdf handler: {str(e)}")
        return {"success": False, "error": str(e)}


async def handle_list_pdfs(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle list PDFs tool.
    
    Args:
        arguments: Empty dictionary
        
    Returns:
        List of documents
    """
    try:
        documents = pdf_processor.list_documents()
        return {"success": True, "documents": documents}

    except Exception as e:
        logger.error(f"Error in list_pdfs handler: {str(e)}")
        return {"success": False, "error": str(e)}
