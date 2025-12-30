"""
Configuration settings for Market Trend Analyzer RAG
Supports both Azure services and local development
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# API Keys & Endpoints
# ============================================

# OpenAI (standard API - recommended for hybrid approach)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Azure OpenAI (alternative - requires approval)
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
USE_AZURE_OPENAI = os.getenv("USE_AZURE_OPENAI", "false").lower() == "true"

# Azure AI Search
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "market-news")

# NewsAPI
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# ============================================
# Model Settings
# ============================================

# OpenAI models
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# Azure OpenAI deployment names (if using Azure)
AZURE_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
AZURE_LLM_DEPLOYMENT = os.getenv("AZURE_LLM_DEPLOYMENT", "gpt-4")

# ============================================
# RAG Settings
# ============================================

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
TOP_K = int(os.getenv("TOP_K", "5"))

# ============================================
# News Categories
# ============================================

NEWS_QUERIES = [
    "stock market",
    "federal reserve interest rates",
    "inflation economic",
    "tech stocks earnings",
    "S&P 500 dow jones",
    "cryptocurrency bitcoin",
    "oil prices energy",
    "employment jobs report"
]

# ============================================
# Validation
# ============================================

def validate_config():
    """Validate required configuration is present"""
    errors = []
    
    # Check for LLM API key
    if not OPENAI_API_KEY and not (USE_AZURE_OPENAI and AZURE_OPENAI_API_KEY):
        errors.append("Missing OPENAI_API_KEY or Azure OpenAI credentials")
    
    # Check for Azure Search (required for hybrid approach)
    if not AZURE_SEARCH_ENDPOINT or not AZURE_SEARCH_API_KEY:
        errors.append("Missing AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_API_KEY")
    
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True


def get_config_summary():
    """Return a summary of current configuration"""
    return {
        "llm_provider": "Azure OpenAI" if USE_AZURE_OPENAI else "OpenAI",
        "llm_model": AZURE_LLM_DEPLOYMENT if USE_AZURE_OPENAI else LLM_MODEL,
        "embedding_model": AZURE_EMBEDDING_DEPLOYMENT if USE_AZURE_OPENAI else EMBEDDING_MODEL,
        "vector_store": "Azure AI Search",
        "search_index": AZURE_SEARCH_INDEX_NAME,
        "chunk_size": CHUNK_SIZE,
        "top_k": TOP_K
    }
