# 📈 Market Trend Analyzer RAG

An intelligent RAG (Retrieval-Augmented Generation) application that summarizes and contextualizes stock and economic reports using AI, deployed with production-grade infrastructure.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Orchestrated-326CE5.svg)
![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC.svg)
![Azure](https://img.shields.io/badge/Azure-AI_Search-0078D4.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-10a37f.svg)

## 🎯 Features

- **Production RAG Pipeline**: Hybrid vector + keyword search with Azure AI Search
- **AI-Powered Analysis**: OpenAI GPT-4 for intelligent summarization
- **Infrastructure as Code**: Terraform for Azure resource provisioning
- **Container Orchestration**: Docker + Kubernetes deployment manifests
- **CI/CD Pipeline**: GitHub Actions for automated testing and deployment
- **Source Citations**: Every answer includes clickable source references

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Azure Cloud                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐     ┌──────────────────┐     ┌─────────────────┐ │
│  │  GitHub Actions  │     │    Kubernetes    │     │    OpenAI API   │ │
│  │  (CI/CD)         │────▶│    (Local/AKS)   │────▶│    (GPT-4)      │ │
│  └──────────────────┘     └──────────────────┘     └─────────────────┘ │
│                                   │                                      │
│                                   ▼                                      │
│  ┌──────────────────┐     ┌──────────────────┐     ┌─────────────────┐ │
│  │   Terraform      │     │  Azure AI Search │     │  Azure Blob     │ │
│  │   (IaC)          │────▶│  (Vector Index)  │     │  Storage        │ │
│  └──────────────────┘     └──────────────────┘     └─────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **LLM** | OpenAI GPT-4o-mini | Response generation |
| **Embeddings** | OpenAI text-embedding-3-small | Vector representations |
| **Vector DB** | Azure AI Search | Hybrid search (vector + BM25) |
| **Container** | Docker | Application packaging |
| **Orchestration** | Kubernetes | Container orchestration |
| **IaC** | Terraform | Azure resource provisioning |
| **CI/CD** | GitHub Actions | Automated pipeline |
| **UI** | Streamlit | Web interface |

## 📁 Project Structure

```
market-trend-analyzer-rag/
├── .github/
│   └── workflows/
│       └── ci-cd.yaml          # GitHub Actions pipeline
├── terraform/
│   ├── main.tf                 # Azure resources (AI Search, Storage)
│   └── terraform.tfvars.example
├── k8s/
│   ├── deployment.yaml         # Kubernetes deployment + service
│   ├── configmap.yaml          # Non-sensitive config
│   ├── secrets.yaml.template   # Secrets template
│   └── ingress.yaml            # Optional ingress config
├── src/
│   ├── __init__.py
│   ├── config.py               # Configuration management
│   ├── data_loader.py          # News fetching & processing
│   ├── embeddings.py           # OpenAI embeddings
│   ├── vector_store.py         # Azure AI Search operations
│   └── rag_pipeline.py         # Core RAG logic
├── data/
│   └── articles.json           # Sample/cached articles
├── Dockerfile                  # Multi-stage production build
├── docker-compose.yml          # Local development
├── requirements.txt
├── app.py                      # Streamlit application
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker Desktop (with Kubernetes enabled)
- Azure CLI (`az`)
- Terraform CLI
- OpenAI API Key
- Azure Subscription (free tier works)

### Option 1: Local Development (Docker Compose)

```bash
# 1. Clone and enter directory
git clone https://github.com/yourusername/market-trend-analyzer-rag.git
cd market-trend-analyzer-rag

# 2. Copy environment template
cp .env.example .env
# Edit .env with your API keys

# 3. Run with Docker Compose
docker-compose up --build

# 4. Open http://localhost:8501
```

### Option 2: Full Infrastructure Setup

#### Step 1: Provision Azure Resources with Terraform

```bash
# Login to Azure
az login

# Initialize and apply Terraform
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars if needed

terraform init
terraform plan
terraform apply

# Get outputs for your .env file
terraform output -json
```

#### Step 2: Configure Environment

```bash
# Copy the Terraform outputs to your .env
cd ..
cp .env.example .env

# Add values from terraform output:
# - AZURE_SEARCH_ENDPOINT
# - AZURE_SEARCH_API_KEY (run: terraform output -raw search_admin_key)
```

#### Step 3: Build and Run with Docker

```bash
# Build the image
docker build -t market-trend-analyzer:latest .

# Run locally
docker run -p 8501:8501 --env-file .env market-trend-analyzer:latest
```

#### Step 4: Deploy to Kubernetes (Local)

```bash
# Enable Kubernetes in Docker Desktop first

# Create namespace
kubectl apply -f k8s/deployment.yaml

# Create configmap
kubectl apply -f k8s/configmap.yaml

# Create secrets (edit the template first!)
cp k8s/secrets.yaml.template k8s/secrets.yaml
# Edit k8s/secrets.yaml with your actual keys
kubectl apply -f k8s/secrets.yaml

# Check deployment
kubectl get pods -n market-trend
kubectl get services -n market-trend

# Access the app (find the port)
kubectl get svc -n market-trend
# Open http://localhost:<NodePort>
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `AZURE_SEARCH_ENDPOINT` | Yes | Azure AI Search endpoint URL |
| `AZURE_SEARCH_API_KEY` | Yes | Azure AI Search admin key |
| `AZURE_SEARCH_INDEX_NAME` | No | Index name (default: market-news) |
| `NEWS_API_KEY` | No | NewsAPI key (sample data included) |
| `LLM_MODEL` | No | OpenAI model (default: gpt-4o-mini) |
| `EMBEDDING_MODEL` | No | Embedding model (default: text-embedding-3-small) |

### Terraform Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `project_name` | market-trend-rag | Resource naming prefix |
| `environment` | dev | Environment tag |
| `location` | eastus | Azure region |
| `search_sku` | free | AI Search tier (free/basic/standard) |

## 📊 Usage

### Example Queries

- "What's the latest news about the stock market?"
- "Summarize recent Federal Reserve news and interest rate updates"
- "What are analysts saying about tech stocks?"
- "Any news about inflation or economic indicators?"
- "What's happening with cryptocurrency markets?"

### Sample Output

```
Question: What's the latest news about Tesla?

Answer: Based on recent articles, Tesla reported Q4 vehicle deliveries 
of 484,000 units, exceeding analyst estimates of 473,000. The company 
benefited from price cuts and strong demand in China. CEO Elon Musk 
reiterated the goal to achieve 2 million annual deliveries in 2025.
[Source: CNBC, 2024-12-21]

Sources:
1. "Tesla Deliveries Beat Expectations in Q4" - CNBC (2024-12-21)
   Relevance Score: 0.92
```

## 🔄 CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci-cd.yaml`) provides:

1. **Test Stage**: Linting (flake8), formatting (black), unit tests
2. **Build Stage**: Multi-stage Docker build, push to GitHub Container Registry
3. **Deploy Stage**: Kubernetes deployment (on main branch)
4. **Terraform Plan**: Infrastructure change preview (on PRs)

### Setting Up CI/CD

Add these secrets to your GitHub repository:

- `AZURE_CREDENTIALS` - Azure service principal JSON
- `ARM_CLIENT_ID`, `ARM_CLIENT_SECRET`, `ARM_SUBSCRIPTION_ID`, `ARM_TENANT_ID` - For Terraform
- `KUBECONFIG` - Base64-encoded kubeconfig (for K8s deployment)

## 🧪 Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run linting
flake8 src/
black --check src/ app.py
```

### Local Development with Hot Reload

```bash
# Using docker-compose (mounts source for hot reload)
docker-compose up

# Or run directly
pip install -r requirements.txt
streamlit run app.py
```

## 📈 Cost Estimation

| Service | Tier | Estimated Cost |
|---------|------|----------------|
| Azure AI Search | Free | $0/month (50MB, 1 index) |
| Azure AI Search | Basic | ~$75/month (2GB, 15 indexes) |
| OpenAI API | Pay-per-use | ~$1-5/month (demo usage) |
| Azure Storage | Standard LRS | ~$0.02/GB/month |

**Total for Demo/Portfolio: ~$5-10/month** (using free tiers where possible)

## 🚧 Future Enhancements

- [ ] Add SEC filing support (10-K, 10-Q parsing)
- [ ] Implement real-time stock price integration
- [ ] Add conversation memory
- [ ] Deploy to Azure Kubernetes Service (AKS)
- [ ] Add Prometheus metrics and Grafana dashboard
- [ ] Implement A/B testing for RAG parameters

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 👤 Author

**Cielo Bryant**
- LinkedIn: [cielo-bryant](https://linkedin.com/in/cielo-bryant)
- GitHub: [@yourusername](https://github.com/yourusername)

---

*Built as a portfolio project demonstrating production ML infrastructure: Docker, Kubernetes, Terraform, Azure AI Search, and RAG architecture.*

![Alt text](Assets/App%20image%201.png)
![Alt text](Assets/App%20image%202.png)
![Alt text](Assets/App%20image%203.png)
![Alt text](Assets/App%20image%204.png)
![Alt text](Assets/App%20image%205.png)