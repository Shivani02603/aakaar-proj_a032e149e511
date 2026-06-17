import os
import json
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import vector store and embeddings
from .vector_store import VectorStore
from .embeddings import get_embedding

def retrieve_context(query: str, top_k: int = 5, session_id: Optional[str] = None, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve relevant context for a query using vector similarity search.
    
    Args:
        query: User's question
        top_k: Number of chunks to retrieve
        session_id: Optional session ID filter
        user_id: Optional user ID filter
    
    Returns:
        List of relevant chunks with metadata
    """
    try:
        # Get query embedding
        query_embedding = get_embedding([query])[0]
        
        # Search vector store
        vector_store = VectorStore()
        
        # Build filter if session_id or user_id provided
        filter_dict = {}
        if session_id:
            filter_dict['session_id'] = session_id
        if user_id:
            filter_dict['user_id'] = user_id
        
        # Perform search
        results = vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_dict=filter_dict if filter_dict else None
        )
        
        logger.info(f"Retrieved {len(results)} chunks for query: {query[:50]}...")
        return results
        
    except Exception as e:
        logger.error(f"Error retrieving context: {str(e)}")
        return []

def build_prompt(query: str, context_chunks: List[Dict[str, Any]]) -> str:
    """
    Build a prompt for the LLM with context and query.
    
    Args:
        query: User's question
        context_chunks: Retrieved context chunks
    
    Returns:
        Formatted prompt string
    """
    prompt_parts = []
    
    # System instruction
    prompt_parts.append("""You are a helpful data analysis assistant. Your task is to answer questions about data from Excel files.
You will be given relevant context from the data, and you must answer the user's question based ONLY on this context.
If the context doesn't contain enough information to answer the question, say so clearly.
Always cite your sources by referencing the filename and row range provided in the context.""")

    # Add context
    prompt_parts.append("\n=== RELEVANT DATA CONTEXT ===")
    
    for i, chunk in enumerate(context_chunks):
        metadata = chunk.get('metadata', {})
        prompt_parts.append(f"\n[Context {i+1}]")
        prompt_parts.append(f"Source: {metadata.get('filename', 'Unknown')} - {metadata.get('sheet_name', 'Unknown sheet')}")
        prompt_parts.append(f"Row range: {metadata.get('row_range', 'Unknown')}")
        prompt_parts.append(f"Content:\n{chunk.get('text', '')}")
    
    # Add query
    prompt_parts.append("\n=== USER QUESTION ===")
    prompt_parts.append(f"\n{query}")
    
    # Add instructions
    prompt_parts.append("\n=== INSTRUCTIONS ===")
    prompt_parts.append("Please provide a helpful answer based on the context above. Include citations where appropriate.")
    
    return "\n".join(prompt_parts)