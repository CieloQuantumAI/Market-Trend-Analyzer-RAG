# ============================================
# Terraform Configuration for Azure Services
# Market Trend Analyzer RAG
# ============================================

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # Uncomment for remote state (recommended for teams)
  # backend "azurerm" {
  #   resource_group_name  = "tfstate-rg"
  #   storage_account_name = "tfstateXXXXX"
  #   container_name       = "tfstate"
  #   key                  = "market-trend-analyzer.tfstate"
  # }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
    cognitive_account {
      purge_soft_delete_on_destroy = true
    }
  }
}

# ============================================
# Variables
# ============================================

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "market-trend-rag"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "search_sku" {
  description = "Azure AI Search SKU (free, basic, standard)"
  type        = string
  default     = "free"
}

# ============================================
# Local Values
# ============================================

locals {
  resource_prefix = "${var.project_name}-${var.environment}"
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Owner       = "Cielo Bryant"
  }
}

# Random suffix for globally unique names
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# ============================================
# Resource Group
# ============================================

resource "azurerm_resource_group" "main" {
  name     = "${local.resource_prefix}-rg"
  location = var.location
  tags     = local.common_tags
}

# ============================================
# Azure AI Search (Vector Database)
# ============================================

resource "azurerm_search_service" "main" {
  name                = "${local.resource_prefix}-search-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.search_sku

  # Free tier limitations: 1 index, 50MB storage
  # Sufficient for demo/portfolio project

  tags = local.common_tags
}

# ============================================
# Storage Account (for documents/data)
# ============================================

resource "azurerm_storage_account" "main" {
  name                     = "mkttrend${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  
  blob_properties {
    versioning_enabled = true
  }

  tags = local.common_tags
}

resource "azurerm_storage_container" "documents" {
  name                  = "documents"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "processed" {
  name                  = "processed"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# ============================================
# Azure OpenAI (Optional - requires approval)
# Uncomment if you have Azure OpenAI access
# ============================================

# resource "azurerm_cognitive_account" "openai" {
#   name                = "${local.resource_prefix}-openai-${random_string.suffix.result}"
#   location            = azurerm_resource_group.main.location
#   resource_group_name = azurerm_resource_group.main.name
#   kind                = "OpenAI"
#   sku_name            = "S0"
#
#   tags = local.common_tags
# }
#
# resource "azurerm_cognitive_deployment" "gpt4" {
#   name                 = "gpt-4"
#   cognitive_account_id = azurerm_cognitive_account.openai.id
#   
#   model {
#     format  = "OpenAI"
#     name    = "gpt-4"
#     version = "0613"
#   }
#   
#   scale {
#     type = "Standard"
#   }
# }
#
# resource "azurerm_cognitive_deployment" "embedding" {
#   name                 = "text-embedding-ada-002"
#   cognitive_account_id = azurerm_cognitive_account.openai.id
#   
#   model {
#     format  = "OpenAI"
#     name    = "text-embedding-ada-002"
#     version = "2"
#   }
#   
#   scale {
#     type = "Standard"
#   }
# }

# ============================================
# Outputs
# ============================================

output "resource_group_name" {
  description = "Resource group name"
  value       = azurerm_resource_group.main.name
}

output "search_service_name" {
  description = "Azure AI Search service name"
  value       = azurerm_search_service.main.name
}

output "search_endpoint" {
  description = "Azure AI Search endpoint"
  value       = "https://${azurerm_search_service.main.name}.search.windows.net"
}

output "search_admin_key" {
  description = "Azure AI Search admin key"
  value       = azurerm_search_service.main.primary_key
  sensitive   = true
}

output "storage_account_name" {
  description = "Storage account name"
  value       = azurerm_storage_account.main.name
}

output "storage_connection_string" {
  description = "Storage account connection string"
  value       = azurerm_storage_account.main.primary_connection_string
  sensitive   = true
}

# Uncomment if using Azure OpenAI
# output "openai_endpoint" {
#   description = "Azure OpenAI endpoint"
#   value       = azurerm_cognitive_account.openai.endpoint
# }
#
# output "openai_key" {
#   description = "Azure OpenAI key"
#   value       = azurerm_cognitive_account.openai.primary_access_key
#   sensitive   = true
# }
