"""
LangChain Multi-Agent System for PDF Analysis
Implements coordinator, summarizer, and Q&A agents using Gemini AI
"""

import logging
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain import hub

from .config import (
    GOOGLE_API_KEY,
    GEMINI_MODEL,
    GEMINI_TEMPERATURE,
    GEMINI_MAX_TOKENS,
)
from .pdf_processor import pdf_processor

logger = logging.getLogger(__name__)


class PDFAnalysisAgents:
    """Multi-agent system for PDF analysis."""

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=GEMINI_TEMPERATURE,
            max_tokens=GEMINI_MAX_TOKENS,
        )

    def _get_qa_chain(self, document_id: str) -> Optional[RetrievalQA]:
        """
        Create a Q&A chain for a specific document.
        
        Args:
            document_id: Unique identifier for the document
            
        Returns:
            RetrievalQA chain or None
        """
        vector_store = pdf_processor.get_vector_store(document_id)
        if not vector_store:
            return None

        qa_prompt = PromptTemplate(
            template="""You are an AI assistant analyzing a PDF document. Use the following context to answer the question.
If you don't know the answer based on the context, say so. Provide detailed and accurate answers.

Context: {context}

Question: {question}

Answer: Let me analyze the document to answer your question.""",
            input_variables=["context", "question"],
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": qa_prompt},
        )

        return qa_chain

    async def summarizer_agent(
        self, document_id: str, summary_type: str = "detailed"
    ) -> Dict[str, Any]:
        """
        Summarizer Agent: Generates summaries of PDF content.
        
        Args:
            document_id: Unique identifier for the document
            summary_type: Type of summary (brief, detailed, executive)
            
        Returns:
            Dictionary with summary results
        """
        try:
            vector_store = pdf_processor.get_vector_store(document_id)
            if not vector_store:
                return {"success": False, "error": "Document not processed"}

            # Retrieve relevant chunks
            retriever = vector_store.as_retriever(search_kwargs={"k": 20})
            docs = retriever.get_relevant_documents("summary overview main points")

            # Combine document content
            full_text = "\n\n".join([doc.page_content for doc in docs[:15]])

            # Create summary prompt based on type
            if summary_type == "brief":
                prompt = f"""Provide a brief 2-3 paragraph summary of this document:

{full_text}

Focus on the main points and key takeaways."""
            elif summary_type == "executive":
                prompt = f"""Provide an executive summary of this document with:
1. Purpose and scope
2. Key findings
3. Main recommendations
4. Critical insights

Document content:
{full_text}"""
            else:  # detailed
                prompt = f"""Provide a comprehensive detailed summary of this document including:
1. Main topics and themes
2. Key arguments and supporting evidence
3. Important data and statistics
4. Conclusions and implications
5. Notable sections and highlights

Document content:
{full_text}"""

            # Generate summary
            summary = self.llm.invoke(prompt)
            
            return {
                "success": True,
                "summary": summary.content,
                "summary_type": summary_type,
                "document_id": document_id,
            }

        except Exception as e:
            logger.error(f"Error in summarizer agent: {str(e)}")
            return {"success": False, "error": str(e)}

    async def qa_agent(self, document_id: str, query: str) -> Dict[str, Any]:
        """
        Q&A Agent: Answers questions about PDF content.
        
        Args:
            document_id: Unique identifier for the document
            query: User's question
            
        Returns:
            Dictionary with answer and source documents
        """
        try:
            qa_chain = self._get_qa_chain(document_id)
            if not qa_chain:
                return {"success": False, "error": "Document not processed"}

            # Execute Q&A
            result = qa_chain({"query": query})

            # Extract source information
            sources = []
            for doc in result.get("source_documents", []):
                sources.append({
                    "page_number": doc.metadata.get("page_number"),
                    "content_preview": doc.page_content[:200] + "...",
                })

            return {
                "success": True,
                "answer": result["result"],
                "query": query,
                "sources": sources[:3],  # Top 3 sources
                "document_id": document_id,
            }

        except Exception as e:
            logger.error(f"Error in Q&A agent: {str(e)}")
            return {"success": False, "error": str(e)}

    async def extraction_agent(
        self, document_id: str, extraction_type: str
    ) -> Dict[str, Any]:
        """
        Extraction Agent: Extracts specific information from PDF.
        
        Args:
            document_id: Unique identifier for the document
            extraction_type: Type of extraction (key_points, statistics, references, etc.)
            
        Returns:
            Dictionary with extracted information
        """
        try:
            vector_store = pdf_processor.get_vector_store(document_id)
            if not vector_store:
                return {"success": False, "error": "Document not processed"}

            # Define extraction prompts
            extraction_prompts = {
                "key_points": "Extract all key points, main arguments, and important takeaways",
                "statistics": "Extract all numerical data, statistics, percentages, and figures",
                "references": "Extract all references, citations, and sources mentioned",
                "definitions": "Extract all important terms, definitions, and concepts",
                "action_items": "Extract all action items, recommendations, and next steps",
            }

            search_query = extraction_prompts.get(
                extraction_type, "Extract important information"
            )

            # Retrieve relevant content
            retriever = vector_store.as_retriever(search_kwargs={"k": 15})
            docs = retriever.get_relevant_documents(search_query)

            # Combine content
            full_text = "\n\n".join([doc.page_content for doc in docs])

            # Create extraction prompt
            prompt = f"""From the following document content, {search_query}.
Present the information in a clear, organized format with bullet points or numbered lists.

Document content:
{full_text}

Extracted information:"""

            # Generate extraction
            result = self.llm.invoke(prompt)

            return {
                "success": True,
                "extraction_type": extraction_type,
                "extracted_info": result.content,
                "document_id": document_id,
            }

        except Exception as e:
            logger.error(f"Error in extraction agent: {str(e)}")
            return {"success": False, "error": str(e)}

    async def coordinator_agent(
        self, document_id: str, task: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Coordinator Agent: Routes tasks to appropriate specialized agents.
        
        Args:
            document_id: Unique identifier for the document
            task: Type of task (summarize, query, extract)
            **kwargs: Additional arguments for specific agents
            
        Returns:
            Dictionary with task results
        """
        try:
            logger.info(f"Coordinator routing task: {task} for document {document_id}")

            if task == "summarize":
                summary_type = kwargs.get("summary_type", "detailed")
                return await self.summarizer_agent(document_id, summary_type)

            elif task == "query":
                query = kwargs.get("query")
                if not query:
                    return {"success": False, "error": "Query is required"}
                return await self.qa_agent(document_id, query)

            elif task == "extract":
                extraction_type = kwargs.get("extraction_type", "key_points")
                return await self.extraction_agent(document_id, extraction_type)

            elif task == "analyze":
                # Comprehensive analysis using multiple agents
                results = {}
                
                # Get summary
                summary_result = await self.summarizer_agent(document_id, "detailed")
                results["summary"] = summary_result
                
                # Extract key points
                key_points_result = await self.extraction_agent(document_id, "key_points")
                results["key_points"] = key_points_result
                
                # Extract statistics if present
                stats_result = await self.extraction_agent(document_id, "statistics")
                results["statistics"] = stats_result

                return {
                    "success": True,
                    "task": "comprehensive_analysis",
                    "results": results,
                    "document_id": document_id,
                }

            else:
                return {"success": False, "error": f"Unknown task: {task}"}

        except Exception as e:
            logger.error(f"Error in coordinator agent: {str(e)}")
            return {"success": False, "error": str(e)}

    async def multi_document_agent(
        self, document_ids: List[str], query: str
    ) -> Dict[str, Any]:
        """
        Multi-Document Agent: Analyzes and compares multiple documents.
        
        Args:
            document_ids: List of document identifiers
            query: Question or task across documents
            
        Returns:
            Dictionary with comparative analysis
        """
        try:
            results = {}
            
            for doc_id in document_ids:
                qa_result = await self.qa_agent(doc_id, query)
                results[doc_id] = qa_result

            # Synthesize results
            synthesis_prompt = f"""You are analyzing multiple documents. Here are the findings from each document:

{self._format_multi_doc_results(results)}

Question: {query}

Provide a comprehensive answer that synthesizes information from all documents, highlighting:
1. Common themes and findings
2. Differences or contradictions
3. Overall insights
4. Document-specific unique information"""

            synthesis = self.llm.invoke(synthesis_prompt)

            return {
                "success": True,
                "synthesized_answer": synthesis.content,
                "individual_results": results,
                "query": query,
            }

        except Exception as e:
            logger.error(f"Error in multi-document agent: {str(e)}")
            return {"success": False, "error": str(e)}

    def _format_multi_doc_results(self, results: Dict[str, Any]) -> str:
        """Format multi-document results for synthesis."""
        formatted = []
        for doc_id, result in results.items():
            if result.get("success"):
                formatted.append(f"Document {doc_id}:\n{result.get('answer', 'No answer')}\n")
            else:
                formatted.append(f"Document {doc_id}: Error - {result.get('error')}\n")
        return "\n".join(formatted)


# Global agents instance
pdf_agents = PDFAnalysisAgents()
