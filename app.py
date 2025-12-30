"""
Market Trend Analyzer RAG - Streamlit App
Production-ready with Azure AI Search and OpenAI
"""
import streamlit as st
from src.rag_pipeline import query, get_suggested_queries
from src.vector_store import get_index_stats, index_articles, clear_index, create_index
from src.data_loader import load_articles, fetch_and_save
from src.config import get_config_summary, validate_config

# Page config
st.set_page_config(
    page_title="Market Trend Analyzer",
    page_icon="📈",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .source-card {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .metric-card {
        background-color: #e8f4ea;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    .config-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        margin: 2px;
    }
    .badge-azure {
        background-color: #0078d4;
        color: white;
    }
    .badge-openai {
        background-color: #10a37f;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("📈 Market Trend Analyzer")
st.markdown("*AI-powered financial news analysis using RAG with Azure AI Search*")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Show config summary
    config = get_config_summary()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**LLM:** {config['llm_provider']}")
        st.markdown(f"**Model:** {config['llm_model']}")
    with col2:
        st.markdown(f"**Vector DB:** {config['vector_store']}")
        st.markdown(f"**Index:** {config['search_index']}")
    
    st.divider()
    
    st.header("📊 Index Status")
    
    try:
        stats = get_index_stats()
        if "error" in stats and stats["error"] == "Index not found":
            st.warning("Index not created yet")
            stats["total_documents"] = 0
        else:
            st.metric("Indexed Documents", stats.get("total_documents", 0))
            if stats.get("storage_size_bytes", 0) > 0:
                size_kb = stats["storage_size_bytes"] / 1024
                st.caption(f"Storage: {size_kb:.1f} KB")
    except Exception as e:
        st.error(f"Cannot connect to Azure AI Search: {str(e)}")
        st.info("Please check your AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_API_KEY")
        stats = {"total_documents": 0}
    
    st.divider()
    
    st.header("🔧 Data Management")
    
    if st.button("🏗️ Create/Update Index", use_container_width=True):
        with st.spinner("Creating index schema..."):
            try:
                create_index()
                st.success("Index created/updated!")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    if st.button("🔄 Fetch Fresh News", use_container_width=True):
        with st.spinner("Fetching articles from NewsAPI..."):
            try:
                articles = fetch_and_save()
                st.success(f"Fetched {len(articles)} articles!")
            except Exception as e:
                st.error(f"Error fetching: {str(e)}")
    
    if st.button("📥 Index Articles", use_container_width=True):
        with st.spinner("Indexing articles into Azure AI Search..."):
            try:
                articles = load_articles()
                num_docs = index_articles(articles)
                st.success(f"Indexed {num_docs} chunks!")
                st.rerun()
            except FileNotFoundError:
                st.error("No articles found. Fetch news first!")
            except Exception as e:
                st.error(f"Error indexing: {str(e)}")
    
    if st.button("🗑️ Clear Index", use_container_width=True):
        try:
            clear_index()
            st.success("Index cleared!")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    st.divider()
    
    st.header("💡 Example Queries")
    for suggestion in get_suggested_queries()[:5]:
        if st.button(suggestion, key=suggestion, use_container_width=True):
            st.session_state.query_input = suggestion

# Main content
# Check configuration
config_valid = True
try:
    config_valid = validate_config()
except Exception:
    config_valid = False

if not config_valid:
    st.error("⚠️ Configuration Error")
    st.markdown("""
    ### Missing Required Configuration
    
    Please set the following environment variables:
    
    **Required:**
    - `OPENAI_API_KEY` - Your OpenAI API key
    - `AZURE_SEARCH_ENDPOINT` - Azure AI Search endpoint (e.g., https://xxx.search.windows.net)
    - `AZURE_SEARCH_API_KEY` - Azure AI Search admin key
    
    **Optional:**
    - `NEWS_API_KEY` - For fetching live news (sample data included)
    
    See `.env.example` for reference.
    """)

elif stats.get("total_documents", 0) == 0:
    st.warning("⚠️ No documents indexed yet. Use the sidebar to set up your data.")
    st.markdown("""
    ### Getting Started
    1. Click **Create/Update Index** to initialize Azure AI Search
    2. Click **Fetch Fresh News** to download recent financial news (or use sample data)
    3. Click **Index Articles** to process and store them
    4. Start asking questions!
    
    ---
    
    ### Architecture
    ```
    User Query → OpenAI Embeddings → Azure AI Search (Vector) → OpenAI GPT → Response
    ```
    
    **Infrastructure:**
    - 🐳 Docker containerized
    - ☸️ Kubernetes ready
    - 🏗️ Terraform for Azure provisioning
    - 🔄 GitHub Actions CI/CD
    """)

else:
    # Query input
    query_input = st.text_input(
        "Ask a question about market trends:",
        value=st.session_state.get("query_input", ""),
        placeholder="e.g., What's the latest news about the stock market?"
    )
    
    col1, col2 = st.columns([1, 5])
    with col1:
        search_button = st.button("🔍 Analyze", type="primary", use_container_width=True)
    
    if search_button and query_input:
        with st.spinner("Analyzing market trends..."):
            try:
                result = query(query_input)
                
                # Display answer
                st.markdown("### 📝 Analysis")
                st.markdown(result["answer"])
                
                # Display sources
                st.markdown("### 📰 Sources")
                st.caption(f"Retrieved {result['num_chunks_retrieved']} relevant passages from {len(result['sources'])} articles")
                
                for i, source in enumerate(result["sources"], 1):
                    title_display = f"{source['title'][:80]}..." if len(source['title']) > 80 else source['title']
                    with st.expander(f"**{i}. {title_display}**"):
                        st.markdown(f"**Source:** {source['source']}")
                        st.markdown(f"**Published:** {source['published_at']}")
                        if source['relevance_score']:
                            st.markdown(f"**Relevance Score:** {source['relevance_score']:.2f}")
                        st.markdown(f"[Read full article]({source['url']})")
                        
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.exception(e)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 14px;'>
    <strong>Tech Stack:</strong> Docker • Kubernetes • Terraform • Azure AI Search • OpenAI • Streamlit<br>
    Built by <a href='https://linkedin.com/in/cielo-bryant'>Cielo Bryant</a> | 
    <a href='https://github.com/yourusername/market-trend-analyzer-rag'>GitHub</a>
</div>
""", unsafe_allow_html=True)
