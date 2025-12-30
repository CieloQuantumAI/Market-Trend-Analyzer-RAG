"""
Embeddings - Generate embeddings using OpenAI or Azure OpenAI
"""
from openai import OpenAI, AzureOpenAI
from typing import List
import time

from src.config import (
    OPENAI_API_KEY,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    USE_AZURE_OPENAI,
    EMBEDDING_MODEL,
    AZURE_EMBEDDING_DEPLOYMENT
)


def get_client():
    """Get the appropriate OpenAI client"""
    if USE_AZURE_OPENAI:
        return AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version="2024-02-01",
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
    else:
        return OpenAI(api_key=OPENAI_API_KEY)


def get_model_name():
    """Get the appropriate model/deployment name"""
    return AZURE_EMBEDDING_DEPLOYMENT if USE_AZURE_OPENAI else EMBEDDING_MODEL


def get_embedding(text: str) -> List[float]:
    """
    Generate embedding for a single text
    
    Args:
        text: Text to embed
    
    Returns:
        List of floats representing the embedding
    """
    client = get_client()
    
    response = client.embeddings.create(
        input=text,
        model=get_model_name()
    )
    
    return response.data[0].embedding


def get_embeddings_batch(texts: List[str], batch_size: int = 100) -> List[List[float]]:
    """
    Generate embeddings for multiple texts with batching
    
    Args:
        texts: List of texts to embed
        batch_size: Number of texts per batch (OpenAI limit is 2048)
    
    Returns:
        List of embeddings
    """
    client = get_client()
    model = get_model_name()
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        response = client.embeddings.create(
            input=batch,
            model=model
        )
        
        # Sort by index to maintain order
        batch_embeddings = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
        all_embeddings.extend(batch_embeddings)
        
        # Rate limiting
        if i + batch_size < len(texts):
            time.sleep(0.1)
        
        print(f"Embedded {min(i + batch_size, len(texts))}/{len(texts)} texts")
    
    return all_embeddings


def get_embedding_dimension() -> int:
    """Get the dimension of embeddings for the current model"""
    # text-embedding-3-small: 1536, text-embedding-ada-002: 1536
    return 1536


if __name__ == "__main__":
    # Test embedding
    test_text = "The stock market rallied today on positive earnings reports."
    embedding = get_embedding(test_text)
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
