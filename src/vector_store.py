"""
Vector Store - Azure AI Search operations for document storage and retrieval
"""
import json
import requests
from typing import List, Dict, Optional
from datetime import datetime

from src.config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_API_KEY,
    AZURE_SEARCH_INDEX_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)
from src.embeddings import get_embedding, get_embeddings_batch, get_embedding_dimension


# Azure AI Search API version
API_VERSION = "2024-07-01"


def get_headers():
    """Get headers for Azure AI Search API requests"""
    return {
        "Content-Type": "application/json",
        "api-key": AZURE_SEARCH_API_KEY
    }


def create_index():
    """
    Create the Azure AI Search index with vector configuration
    """
    index_schema = {
        "name": AZURE_SEARCH_INDEX_NAME,
        "fields": [
            {"name": "id", "type": "Edm.String", "key": True, "filterable": True},
            {"name": "content", "type": "Edm.String", "searchable": True},
            {"name": "title", "type": "Edm.String", "searchable": True, "filterable": True},
            {"name": "source", "type": "Edm.String", "filterable": True, "facetable": True},
            {"name": "url", "type": "Edm.String", "filterable": True},
            {"name": "published_at", "type": "Edm.String", "filterable": True, "sortable": True},
            {"name": "article_id", "type": "Edm.String", "filterable": True},
            {"name": "chunk_index", "type": "Edm.Int32", "filterable": True},
            {
                "name": "content_vector",
                "type": "Collection(Edm.Single)",
                "dimensions": get_embedding_dimension(),
                "vectorSearchProfile": "vector-profile"
            }
        ],
        "vectorSearch": {
            "algorithms": [
                {
                    "name": "hnsw-algorithm",
                    "kind": "hnsw",
                    "hnswParameters": {
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500,
                        "metric": "cosine"
                    }
                }
            ],
            "profiles": [
                {
                    "name": "vector-profile",
                    "algorithm": "hnsw-algorithm"
                }
            ]
        }
    }
    
    url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX_NAME}?api-version={API_VERSION}"
    
    response = requests.put(url, headers=get_headers(), json=index_schema)
    
    if response.status_code in [200, 201]:
        print(f"Index '{AZURE_SEARCH_INDEX_NAME}' created/updated successfully")
        return True
    else:
        print(f"Error creating index: {response.status_code} - {response.text}")
        return False


def delete_index():
    """Delete the Azure AI Search index"""
    url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX_NAME}?api-version={API_VERSION}"
    
    response = requests.delete(url, headers=get_headers())
    
    if response.status_code in [200, 204]:
        print(f"Index '{AZURE_SEARCH_INDEX_NAME}' deleted successfully")
        return True
    elif response.status_code == 404:
        print(f"Index '{AZURE_SEARCH_INDEX_NAME}' not found")
        return True
    else:
        print(f"Error deleting index: {response.status_code} - {response.text}")
        return False


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks based on approximate token count
    
    Uses simple word-based splitting (1 token ≈ 0.75 words)
    """
    words_per_chunk = int(chunk_size * 0.75)
    overlap_words = int(overlap * 0.75)
    
    words = text.split()
    
    if len(words) <= words_per_chunk:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(words):
        end = start + words_per_chunk
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        
        start = end - overlap_words
        
        if start >= len(words) - overlap_words:
            break
    
    return chunks


def index_articles(articles: List[Dict]) -> int:
    """
    Index articles into Azure AI Search
    
    Args:
        articles: List of article dictionaries
    
    Returns:
        Number of chunks indexed
    """
    # Ensure index exists
    create_index()
    
    all_documents = []
    all_chunks = []
    
    # Prepare documents
    for article in articles:
        chunks = chunk_text(article["content"])
        
        for i, chunk in enumerate(chunks):
            doc_id = f"{article['id']}_{i}"
            
            all_chunks.append(chunk)
            all_documents.append({
                "id": doc_id,
                "content": chunk,
                "title": article.get("title", "")[:500],
                "source": article.get("source", "Unknown"),
                "url": article.get("url", ""),
                "published_at": article.get("published_at", ""),
                "article_id": str(article["id"]),
                "chunk_index": i
            })
    
    # Generate embeddings
    print(f"Generating embeddings for {len(all_chunks)} chunks...")
    embeddings = get_embeddings_batch(all_chunks)
    
    # Add embeddings to documents
    for doc, embedding in zip(all_documents, embeddings):
        doc["content_vector"] = embedding
    
    # Upload in batches (Azure limit is 1000 per batch)
    batch_size = 100
    total_indexed = 0
    
    for i in range(0, len(all_documents), batch_size):
        batch = all_documents[i:i + batch_size]
        
        url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX_NAME}/docs/index?api-version={API_VERSION}"
        
        payload = {
            "value": [{"@search.action": "upload", **doc} for doc in batch]
        }
        
        response = requests.post(url, headers=get_headers(), json=payload)
        
        if response.status_code in [200, 207]:
            total_indexed += len(batch)
            print(f"Indexed {total_indexed}/{len(all_documents)} documents")
        else:
            print(f"Error indexing batch: {response.status_code} - {response.text}")
    
    print(f"Total indexed: {total_indexed} chunks from {len(articles)} articles")
    return total_indexed


def search(query: str, top_k: int = 5) -> List[Dict]:
    """
    Search for relevant chunks using hybrid search (vector + keyword)
    
    Args:
        query: Search query
        top_k: Number of results to return
    
    Returns:
        List of results with documents and scores
    """
    # Generate query embedding
    query_embedding = get_embedding(query)
    
    url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX_NAME}/docs/search?api-version={API_VERSION}"
    
    # Hybrid search: combines vector search with keyword search
    payload = {
        "count": True,
        "top": top_k,
        "select": "id, content, title, source, url, published_at, article_id, chunk_index",
        "vectorQueries": [
            {
                "kind": "vector",
                "vector": query_embedding,
                "fields": "content_vector",
                "k": top_k
            }
        ],
        # Also include keyword search for hybrid results
        "search": query,
        "queryType": "simple"
    }
    
    response = requests.post(url, headers=get_headers(), json=payload)
    
    if response.status_code != 200:
        print(f"Search error: {response.status_code} - {response.text}")
        return []
    
    results = response.json()
    
    formatted_results = []
    for doc in results.get("value", []):
        formatted_results.append({
            "id": doc.get("id"),
            "content": doc.get("content"),
            "metadata": {
                "title": doc.get("title"),
                "source": doc.get("source"),
                "url": doc.get("url"),
                "published_at": doc.get("published_at"),
                "article_id": doc.get("article_id"),
                "chunk_index": doc.get("chunk_index")
            },
            "score": doc.get("@search.score", 0)
        })
    
    return formatted_results


def get_index_stats() -> Dict:
    """Get statistics about the index"""
    url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX_NAME}/stats?api-version={API_VERSION}"
    
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        stats = response.json()
        return {
            "total_documents": stats.get("documentCount", 0),
            "storage_size_bytes": stats.get("storageSize", 0),
            "index_name": AZURE_SEARCH_INDEX_NAME
        }
    elif response.status_code == 404:
        return {
            "total_documents": 0,
            "storage_size_bytes": 0,
            "index_name": AZURE_SEARCH_INDEX_NAME,
            "error": "Index not found"
        }
    else:
        return {
            "total_documents": 0,
            "error": f"Error: {response.status_code}"
        }


def clear_index():
    """Clear all documents from the index by deleting and recreating it"""
    delete_index()
    create_index()
    print("Index cleared and recreated")


if __name__ == "__main__":
    # Test index operations
    stats = get_index_stats()
    print(f"Index stats: {stats}")
