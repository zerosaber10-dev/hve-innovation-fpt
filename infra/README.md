# Azure Infrastructure as Code (Bicep)

This folder contains the complete Azure Bicep infrastructure definitions for the Enterprise HR Time and Leave Copilot.

## Files

* [`main.bicep`](main.bicep): Root Bicep template defining App Service, Azure Functions, Cosmos DB (2 separate stores), Azure AI Search, Service Bus, Key Vault, Azure AI Foundry/Cognitive Services, Azure Bot Service, and least-privilege RBAC role assignments with zero hardcoded secrets.
* [`main.bicepparam`](main.bicepparam): Environment parameter file for non-production/test deployment.

## Validation & Compilation

```bash
# Compile and validate Bicep template
az bicep build --file main.bicep

# Compile and validate parameter file
az bicep build-params --file main.bicepparam
```

For complete architecture, least-privilege RBAC matrix, and deployment guide, refer to [`docs/deployment/azure-teams-deployment.md`](../docs/deployment/azure-teams-deployment.md).
