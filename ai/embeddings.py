import os
from typing import List
import openai
from openai import OpenAI

class EmbeddingClient:
    """Client for OpenAI text-embedding-3-small model."""
    
    def __init__(self):
        self._client = None
        self.model = "text-embedding-3-small"
        self.dimension = 1536  # From AI SPEC
        
    @property
    def client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            self._client = OpenAI(api_key=api_key)
        return self._client
    
    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string."""
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of text strings."""
        if not texts:
            return []
        
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
            encoding_format="float"
        )
        
        # Sort embeddings to match input order
        embeddings_by_index = {item.index: item.embedding for item in response.data}
        embeddings = [embeddings_by_index[i] for i in range(len(texts))]
        return embeddings

def get_embedding(texts: List[str]) -> List[List[float]]:
    """Module-level function to get embeddings for a list of texts.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors (each vector is List[float] of length 1536)
    """
    client = EmbeddingClient()
    return client.embed_batch(texts)