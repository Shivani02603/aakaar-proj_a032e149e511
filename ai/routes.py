from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import logging

from ai.ingest import ingest_excel
from ai.rag import answer_question

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/ai', tags=['AI'])

class IngestRequest(BaseModel):
    session_id: str = Field(..., description="ID of the user session")
    filename: Optional[str] = Field(None, description="Original filename")

class IngestResponse(BaseModel):
    success: bool
    message: str
    file_id: Optional[str] = None
    chunk_count: Optional[int] = None

class QueryRequest(BaseModel):
    session_id: str = Field(..., description="ID of the user session")
    question: str = Field(..., description="User's natural language question")
    file_ids: Optional[List[str]] = Field(None, description="Optional list of file IDs to restrict search")

class SourceCitation(BaseModel):
    file_id: str
    filename: str
    sheet_name: str
    row_start: int
    row_end: int
    chunk_text: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    session_id: str
    question: str
    answer_id: str

@router.post("/ingest", response_model=IngestResponse)
async def ingest_file(
    session_id: str,
    file: UploadFile = File(...),
    filename: Optional[str] = None
):
    """
    Endpoint to upload and ingest an Excel file.
    """
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")
    
    try:
        # Read file content
        contents = await file.read()
        
        # Generate a file ID if not provided via form
        file_id = str(uuid.uuid4())
        actual_filename = filename or file.filename
        
        # Call ingestion pipeline
        chunk_count = ingest_excel(
            file_content=contents,
            filename=actual_filename,
            session_id=session_id,
            file_id=file_id
        )
        
        return IngestResponse(
            success=True,
            message=f"Successfully ingested {actual_filename}",
            file_id=file_id,
            chunk_count=chunk_count
        )
        
    except Exception as e:
        logger.error(f"Error ingesting file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest file: {str(e)}")

@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Endpoint to ask a question about ingested documents.
    """
    try:
        # Generate answer ID
        answer_id = str(uuid.uuid4())
        
        # Call RAG pipeline
        answer, sources = answer_question(
            question=request.question,
            session_id=request.session_id,
            file_ids=request.file_ids
        )
        
        # Convert sources to response format
        source_citations = []
        for source in sources:
            citation = SourceCitation(
                file_id=source.get('file_id', ''),
                filename=source.get('filename', ''),
                sheet_name=source.get('sheet_name', ''),
                row_start=source.get('row_start', 0),
                row_end=source.get('row_end', 0),
                chunk_text=source.get('chunk_text', '')[:200] + "..."  # Truncate for response
            )
            source_citations.append(citation)
        
        return QueryResponse(
            answer=answer,
            sources=source_citations,
            session_id=request.session_id,
            question=request.question,
            answer_id=answer_id
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")