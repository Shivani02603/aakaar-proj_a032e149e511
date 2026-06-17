import os
import pandas as pd
import uuid
from typing import List, Dict, Any, Tuple
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import vector store and embeddings (circular imports handled via local imports)
from .vector_store import VectorStore
from .embeddings import get_embedding

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Recursive chunking strategy for text.
    Splits text into chunks of approximately chunk_size characters with overlap.
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # Try to find a good break point (space, newline, period)
        break_point = text.rfind(' ', start, end)
        if break_point == -1:
            break_point = text.rfind('\n', start, end)
        if break_point == -1:
            break_point = text.rfind('.', start, end)
        if break_point == -1 or break_point < start + chunk_size // 2:
            break_point = end
        
        chunks.append(text[start:break_point].strip())
        start = break_point - chunk_overlap
        if start < 0:
            start = 0
    
    return chunks

def process_excel_sheet(df: pd.DataFrame, sheet_name: str) -> List[Dict[str, Any]]:
    """
    Convert an Excel sheet DataFrame into text chunks with metadata.
    """
    chunks = []
    
    # Convert DataFrame to text representation
    text_content = f"Sheet: {sheet_name}\n\n"
    
    # Add column names
    text_content += "Columns: " + ", ".join(df.columns.tolist()) + "\n\n"
    
    # Add data rows
    for idx, row in df.iterrows():
        row_text = f"Row {idx + 1}: "
        row_values = []
        for col in df.columns:
            value = row[col]
            if pd.isna(value):
                value = ""
            row_values.append(f"{col}: {value}")
        row_text += "; ".join(row_values)
        text_content += row_text + "\n"
    
    # Chunk the text
    text_chunks = chunk_text(text_content, chunk_size=1000, chunk_overlap=200)
    
    # Create chunk objects with metadata
    for i, chunk_text in enumerate(text_chunks):
        chunk_id = str(uuid.uuid4())
        chunks.append({
            'id': chunk_id,
            'text': chunk_text,
            'chunk_index': i,
            'sheet_name': sheet_name,
            'total_chunks': len(text_chunks),
            'row_range': f"Rows 1-{len(df)}"  # Simplified row range
        })
    
    return chunks

def ingest_excel(file_path: str, session_id: str, user_id: str) -> Dict[str, Any]:
    """
    Main ingestion function for Excel files.
    
    Args:
        file_path: Path to the Excel file
        session_id: Current session ID
        user_id: User ID
    
    Returns:
        Dictionary with ingestion results
    """
    try:
        # Read Excel file
        logger.info(f"Ingesting Excel file: {file_path}")
        excel_file = pd.ExcelFile(file_path)
        
        all_chunks = []
        sheet_metadata = []
        
        # Process each sheet
        for sheet_name in excel_file.sheet_names:
            logger.info(f"Processing sheet: {sheet_name}")
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # Get sheet metadata
            sheet_metadata.append({
                'sheet_name': sheet_name,
                'rows': len(df),
                'columns': len(df.columns),
                'columns_list': df.columns.tolist()
            })
            
            # Process sheet into chunks
            sheet_chunks = process_excel_sheet(df, sheet_name)
            all_chunks.extend(sheet_chunks)
        
        # Get embeddings for all chunks
        logger.info(f"Generating embeddings for {len(all_chunks)} chunks")
        
        # Get embeddings in batches to avoid rate limits
        batch_size = 50
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i + batch_size]
            batch_texts = [chunk['text'] for chunk in batch]
            
            # Get embeddings
            embeddings = get_embedding(batch_texts)
            
            # Add embeddings to chunks
            for j, chunk in enumerate(batch):
                chunk['embedding'] = embeddings[j]
        
        # Store in vector database
        logger.info("Storing chunks in vector database")
        vector_store = VectorStore()
        
        # Prepare documents for storage
        documents = []
        for chunk in all_chunks:
            documents.append({
                'id': chunk['id'],
                'text': chunk['text'],
                'embedding': chunk['embedding'],
                'metadata': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'chunk_index': chunk['chunk_index'],
                    'sheet_name': chunk['sheet_name'],
                    'total_chunks': chunk['total_chunks'],
                    'row_range': chunk['row_range'],
                    'filename': os.path.basename(file_path),
                    'ingested_at': datetime.utcnow().isoformat()
                }
            })
        
        # Upsert documents
        vector_store.upsert(documents)
        
        logger.info(f"Successfully ingested {len(all_chunks)} chunks from {len(sheet_metadata)} sheets")
        
        return {
            'success': True,
            'chunks_ingested': len(all_chunks),
            'sheets_processed': len(sheet_metadata),
            'sheet_metadata': sheet_metadata,
            'filename': os.path.basename(file_path)
        }
        
    except Exception as e:
        logger.error(f"Error ingesting Excel file: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'filename': os.path.basename(file_path)
        }