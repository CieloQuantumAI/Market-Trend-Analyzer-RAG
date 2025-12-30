"""
RAG Pipeline - Core retrieval-augmented generation logic
Using OpenAI or Azure OpenAI for generation
"""
from openai import OpenAI, AzureOpenAI
from typing import List, Dict
from datetime import datetime

from src.config import (
    OPENAI_API_KEY,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    USE_AZURE_OPENAI,
    LLM_MODEL,
    AZURE_LLM_DEPLOYMENT,
    TOP_K
)
from src.vector_store import search, get_index_stats


def get_llm_client():
    """Get the appropriate OpenAI client for LLM"""
    if USE_AZURE_OPENAI:
        return AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version="2024-02-01",
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
    else:
        return OpenAI(api_key=OPENAI_API_KEY)


def get_llm_model():
    """Get the appropriate model/deployment name"""
    return AZURE_LLM_DEPLOYMENT if USE_AZURE_OPENAI else LLM_MODEL


SYSTEM_PROMPT = """You are a financial market analyst assistant. Your role is to analyze and summarize market news and economic trends based on the provided context.

Guidelines:
1. Only use information from the provided context to answer questions
2. If the context doesn't contain relevant information, say so clearly
3. Cite your sources by mentioning the article title or source
4. Provide clear, concise summaries
5. Highlight key trends, numbers, and insights
6. If asked about specific stocks or sectors, focus on relevant information
7. Be objective and avoid speculation beyond what the sources state

Current date: {current_date}
"""


def build_context(retrieved_chunks: List[Dict]) -> str:
    """
    Build context string from retrieved chunks
    """
    if not retrieved_chunks:
        return "No relevant articles found."
    
    context_parts = []
    seen_articles = set()
    
    for i, chunk in enumerate(retrieved_chunks, 1):
        article_id = chunk["metadata"].get("article_id", "")
        title = chunk["metadata"].get("title", "Unknown")
        source = chunk["metadata"].get("source", "Unknown")
        published = chunk["metadata"].get("published_at", "")[:10]
        
        # Add article header only once per article
        if article_id not in seen_articles:
            context_parts.append(f"\n--- Source {i}: {title} ({source}, {published}) ---")
            seen_articles.add(article_id)
        
        context_parts.append(chunk["content"])
    
    return "\n".join(context_parts)


def build_messages(query: str, context: str) -> List[Dict]:
    """Build the messages for the chat completion"""
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT.format(current_date=datetime.now().strftime("%Y-%m-%d"))
        },
        {
            "role": "user",
            "content": f"""Based on the following financial news articles, please answer the question.

CONTEXT:
{context}

QUESTION: {query}

Please provide a comprehensive answer based on the context above. Include relevant details and cite the sources when possible."""
        }
    ]


def generate_response(query: str, context: str) -> str:
    """
    Generate response using OpenAI/Azure OpenAI
    """
    client = get_llm_client()
    messages = build_messages(query, context)
    
    response = client.chat.completions.create(
        model=get_llm_model(),
        messages=messages,
        temperature=0.7,
        max_tokens=1000
    )
    
    return response.choices[0].message.content


def query(question: str, top_k: int = TOP_K) -> Dict:
    """
    Main RAG query function
    
    Args:
        question: User's question
        top_k: Number of chunks to retrieve
    
    Returns:
        Dictionary with response and sources
    """
    # Step 1: Retrieve relevant chunks
    retrieved_chunks = search(question, top_k=top_k)
    
    # Step 2: Build context
    context = build_context(retrieved_chunks)
    
    # Step 3: Generate response
    response = generate_response(question, context)
    
    # Step 4: Format sources for citation
    sources = []
    seen_urls = set()
    for chunk in retrieved_chunks:
        url = chunk["metadata"].get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            sources.append({
                "title": chunk["metadata"].get("title", "Unknown"),
                "source": chunk["metadata"].get("source", "Unknown"),
                "url": url,
                "published_at": chunk["metadata"].get("published_at", "")[:10],
                "relevance_score": chunk.get("score", 0)
            })
    
    return {
        "question": question,
        "answer": response,
        "sources": sources,
        "num_chunks_retrieved": len(retrieved_chunks)
    }


def get_suggested_queries() -> List[str]:
    """Return a list of suggested queries for the UI"""
    return [
        "What's the latest news about the stock market?",
        "Summarize recent Federal Reserve news and interest rate updates",
        "What are analysts saying about tech stocks?",
        "Any news about inflation or economic indicators?",
        "What's happening with cryptocurrency markets?",
        "Summarize recent earnings reports",
        "What are the current market trends?",
        "Any news about the S&P 500?"
    ]


if __name__ == "__main__":
    # Test query
    stats = get_index_stats()
    print(f"Index stats: {stats}")
    
    if stats.get("total_documents", 0) > 0:
        test_question = "What's the latest market news?"
        result = query(test_question)
        print(f"\nQuestion: {result['question']}")
        print(f"\nAnswer: {result['answer']}")
        print(f"\nSources: {len(result['sources'])}")
        for source in result['sources']:
            print(f"  - {source['title']} ({source['source']})")
    else:
        print("No documents indexed. Run data indexing first.")
