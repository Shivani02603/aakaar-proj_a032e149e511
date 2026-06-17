import os
import uuid
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import Json
import numpy as np

class VectorStore:
    """PostgreSQL pgvector store for document chunks."""
    
    def __init__(self):
        self._connection = None
        self.dimension = 1536  # From AI SPEC
        
    @property
    def connection(self):
        """Lazy initialization of PostgreSQL connection."""
        if self._connection is None:
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME", "ragdb")
            db_user = os.getenv("DB_USER", "postgres")
            db_password = os.getenv("DB_PASSWORD", "")
            
            conn_string = f"host={db_host} port={db_port} dbname={db_name} user={db_user} password={db_password}"
            self._connection = psycopg2.connect(conn_string)
            
            # Enable pgvector extension
            with self._connection.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                self._connection.commit()
                
            # Create table if not exists
            self._create_table()
            
        return self._connection
    
    def _create_table(self):
        """Create the document_chunks table with vector column."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS document_chunks (
            id UUID PRIMARY KEY,
            embedding vector(1536),
            metadata JSONB,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
        ON document_chunks USING ivfflat (embedding vector_cosine_ops);
        """
        
        with self.connection.cursor() as cur:
            cur.execute(create_table_sql)
            self.connection.commit()
    
    def upsert(self, id: str, vector: List[float], metadata: Dict[str, Any], content: str):
        """Insert or update a vector with metadata and content."""
        # Convert to numpy array for pgvector
        vector_array = np.array(vector, dtype=np.float32)
        
        upsert_sql = """
        INSERT INTO document_chunks (id, embedding, metadata, content)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            embedding = EXCLUDED.embedding,
            metadata = EXCLUDED.metadata,
            content = EXCLUDED.content;
        """
        
        with self.connection.cursor() as cur:
            cur.execute(upsert_sql, (id, vector_array, Json(metadata), content))
            self.connection.commit()
    
    def search(self, query_embedding: List[float], top_k: int = 5, **filters) -> List[Dict[str, Any]]:
        """Search for similar vectors using cosine similarity.
        
        Args:
            query_embedding: The query embedding vector
            top_k: Number of results to return (default: 5 from AI SPEC)
            **filters: Optional metadata filters (e.g., filename='data.xlsx')
            
        Returns:
            List of matches with id, content, metadata, and similarity score
        """
        # Convert to numpy array for pgvector
        query_array = np.array(query_embedding, dtype=np.float32)
        
        # Build WHERE clause for filters
        where_clauses = []
        filter_values = []
        
        for key, value in filters.items():
            where_clauses.append(f"metadata->>%s = %s")
            filter_values.extend([key, str(value)])
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"
        
        search_sql = f"""
        SELECT 
            id,
            content,
            metadata,
            1 - (embedding <=> %s) as similarity
        FROM document_chunks
        WHERE {where_sql}
        ORDER BY embedding <=> %s
        LIMIT %s;
        """
        
        with self.connection.cursor() as cur:
            params = [query_array, query_array, top_k]
            if filter_values:
                params = filter_values + params
            cur.execute(search_sql, params)
            
            results = []
            for row in cur.fetchall():
                results.append({
                    "id": str(row[0]),
                    "content": row[1],
                    "metadata": row[2],
                    "similarity": float(row[3])
                })
            
            return results
    
    def close(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None