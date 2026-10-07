# Microsoft Commercial Marketplace Managed Application Publishing & Operations Guide

This operational guide provides end-to-end technical and governance instructions for publishing the **Enterprise HR Time and Leave Copilot** as an Azure Managed Application offer in **Microsoft Partner Center**, achieving IP Co-sell eligibility, and managing customer tenant lifecycles.

---

## 1. Executive Summary & Delivery Model

The Enterprise HR Time and Leave Copilot is packaged as an **Azure Managed Application**, enabling automated, turnkey infrastructure and container provisioning directly inside customer Azure subscriptions while preserving complete data sovereignty.

### Customer Subscription & Managed Resource Group (MRG) Boundary

* **Customer Resource Group**: Contains the `Microsoft.Solutions/applications` resource definition representing the customer's purchase and offer binding.
* **Managed Resource Group (MRG)**: Contains all runtime cloud infrastructure resources (`Microsoft.Web/sites`, `Microsoft.DocumentDB/databaseAccounts`, `Microsoft.Search/searchServices`, `Microsoft.ServiceBus/namespaces`, `Microsoft.KeyVault/vaults`).
* **Platform Deny Assignment**: Azure automatically places a system-level Deny Assignment (`Microsoft.Resources/denyAssignments`) over the MRG. This prevents customer administrators from modifying, reconfiguring, or accidentally deleting internal Copilot infrastructure components.
* **Immutable Container Runtime**: Because external CI/CD file system writes (such as Kudu zipdeploy) are rejected by the MRG Deny Assignment with `403 Forbidden`, the application runtime is deployed via immutable Linux Docker containers (`linuxFxVersion: 'DOCKER|${containerImage}'`). Azure App Service directly pulls and mounts the container image from the registry, bypassing file-system write locks entirely.

```mermaid
flowchart TB
    subgraph CustomerSub ["Customer Azure Subscription"]
        subgraph CustRG ["Customer Resource Group"]
            managedApp["Microsoft.Solutions/applications\n(HR Copilot Managed Application)"]
        end

        subgraph MRG ["Managed Resource Group (MRG) - Deny Assignment Enabled"]
            direction TB
            appService["Azure App Service (Linux Container)\n- FastAPI ASGI Web Host (:8000)\n- Bot Framework Webhook (/api/messages)\n- Health / Readiness Probes (/healthz, /readyz)"]
            funcApp["Azure Functions (Linux)\n- Service Bus SLA Timer & Escalation Trigger"]
            cosmos["Azure Cosmos DB (Serverless SQL)\n- Tickets & Memory Databases"]
            aiSearch["Azure AI Search (Standard SKU)\n- BM25 + Vector Policy Retrieval"]
            sb["Azure Service Bus (Standard)\n- hr-sla-jobs Queue"]
            kv["Azure Key Vault (RBAC)\n- Zero Hardcoded Secrets"]

            appService --> cosmos
            appService --> aiSearch
            appService --> sb
            sb --> funcApp
            funcApp --> cosmos
            appService -.-> kv
            funcApp -.-> kv
        end
    end

    subgraph PublisherTenant ["Publisher Entra ID Tenant"]
        publisherOps["Publisher Support & Operations Team"]
        jitEngine["Azure JIT Access Approval Service"]
    end

    CustomerSub <==>|Customer Owns Data Plane & Billing| MRG
    publisherOps -.->|Time-Bound JIT Request (Max 8 Hours)| jitEngine
    jitEngine ==>|Temporary Contributor RBAC| MRG

    classDef mrgBox fill:#e7f5ff,stroke:#1971c2,stroke-width:2px;
    classDef pubBox fill:#fff3bf,stroke:#f08c00,stroke-width:2px;
    class MRG mrgBox;
    class PublisherTenant pubBox;
```

---

## 2. Partner Center Technical Configuration Contract

When configuring an **Azure Application** offer in Microsoft Partner Center under the **Plan setup** tab, configure the plan type as **Managed Application**.

### Publisher Authorizations Array

To enable publisher maintenance, troubleshooting, and support within the customer's MRG, Partner Center requires an authorization array defining which publisher identities receive role-based access control (RBAC):

| Configuration Field | Technical Specification | Rationale & Governance |
|---|---|---|
| **Publisher Entra ID Tenant ID** | Publisher Tenant GUID (e.g., `72f988bf-86f1-41af-91ab-2d7cd011db47`) | Establishes the authoritative tenant trust boundary. |
| **Principal Security Group ID** | Entra ID Security Group Object ID | Do **NOT** assign individual user accounts. Always use a dedicated Entra ID Security Group (e.g., `HR-Copilot-ManagedApp-Tier3Support`). |
| **Role Definition** | `Contributor` (`b24988ac-6180-42a0-ab88-20f7382dd24c`) | Grants operational management rights across MRG resources without subscription-level privilege escalation. |

### Just-In-Time (JIT) Access Governance

To satisfy enterprise customer security and compliance requirements (SOC 2, ISO 27001, HIPAA), Managed Applications must enforce Just-In-Time (JIT) access rather than standing permissions:

1. **JIT Enablement**: In Partner Center Plan Technical Configuration, check **Enable Just-In-Time (JIT) access**.
2. **Maximum Session Duration**: Configure maximum JIT session window to **8 hours**. Support personnel must re-request authorization for extended troubleshooting sessions.
3. **Approval Model**:
   * **Customer Approval (Recommended)**: The customer receives an approval notification in the Azure Portal whenever publisher support requests MRG elevation.
   * **Auto-Approval**: Suitable only for managed service tiers with explicit contractual SLAs where customer approval delay would violate response guarantees.
4. **Auditability**: Every JIT elevation event, token issuance, and resource modification is logged in the customer's Azure Activity Log and Microsoft Entra ID PIM audit history.

---

## 3. Package Assembly & Verification Pipeline

Managed Application packages uploaded to Partner Center must be packaged into a single root-level ZIP archive named `app.zip`.

### Package Structure Requirements

The `app.zip` archive must contain exactly two files located at the root of the ZIP file:
```text
app.zip
├── mainTemplate.json        # Compiled ARM deployment template
└── createUiDefinition.json  # Azure Portal deployment wizard definition
```

> [!IMPORTANT]
> The ZIP archive must **never** contain nested directories (e.g., `app/mainTemplate.json`) or operating system metadata files (`.DS_Store`, `Thumbs.db`). Nested files cause immediate automated rejection during Partner Center package ingestion.

### Automated Packaging and Verification Command

Execute the repository packaging CLI utility to validate schema compliance, parameter parity, container deployment settings, and zero hardcoded secrets:

```bash
uv run python packaging/managed_app/package_managed_app.py --summary-json packaging/managed_app/verification_summary.json
```

Output:
```text
=== Azure Managed Application Validator & Packager ===
Checking template: infra\mainTemplate.json
  [PASS] mainTemplate.json is valid and contains zero secrets.
Checking UI definition: infra\createUiDefinition.json
  [PASS] createUiDefinition.json conforms to schema and zero secrets.
Checking App Service container deployment configuration in ARM template...
  [PASS] App Service Linux container configuration verified.
Checking parameter parity between UI outputs and template parameters...
  [PASS] Parameter parity confirmed (8 outputs mapped).
Building Managed Application package: packaging\managed_app\app.zip
  [PASS] Package successfully created: packaging\managed_app\app.zip
         File size: 6,468 bytes
  [PASS] Summary JSON written: packaging/managed_app/verification_summary.json
```

### Parameter Parity Rules

* **Parity Invariant**: Every output declared in `createUiDefinition.json` must map to a parameter in `mainTemplate.json`.
* **Default Values**: Template parameters with a `defaultValue` (such as `containerImage`) do not require user prompt elements in `createUiDefinition.json`, preserving a clean wizard UX while allowing ARM overrides.
* **Zero Secrets**: Neither template nor UI definition may contain plaintext passwords, API keys, connection strings, or bearer tokens. All inter-service communication utilizes Entra ID Managed Identities and RBAC role assignments.

---

## 4. Offer Setup, Pricing, & Metering Dimensions

### Offer Types and Commercial Setup

1. **Offer Type**: In Partner Center, create a new offer of type **Azure Application**.
2. **Offer Setup**:
   * Select **Sell through Microsoft** to enable Azure Marketplace invoicing and MACC (Microsoft Azure Consumption Commitment) decrement for enterprise buyers.
   * Configure Leads Management connecting to CRM (Dynamics 365, Salesforce, or HTTPS webhook).

### Plan Pricing Models

Managed Applications support three flexible monetization structures:
1. **Flat Rate Monthly / Annual Subscription**: Fixed billing per tenant deployment.
2. **Tiered Capacity**: Multiple plans (Dev/Test B1 SKU vs Enterprise P1v3 SKU) defined via `appServicePlanSku` options.
3. **Marketplace Metering Service API**: Emit custom usage events for consumption billing:
   * Dimension `active_employee_seats`: Billed per active user engaging the Copilot per month.
   * Dimension `processed_leave_tickets`: Billed per automated ticket lifecycle transition.

---

## 5. Deployment Verification & Private Audience Testing

Before submitting the offer for public certification, test the deployment end-to-end using a **Private Audience**:

### Step 1: Add Private Audience Subscription
In Partner Center, navigate to **Plan Overview** -> **Private Audience** and add your test Azure Subscription ID.

### Step 2: Customer Portal Deployment Test
1. Access the Azure Portal using the private preview link.
2. Complete the deployment wizard:
   * `environmentName`: `test`
   * `appNamePrefix`: `hr-time-leave`
   * `entraTenantId`: Test tenant ID
   * `appServicePlanSku`: `B1`
   * `searchSku`: `standard`
3. Verify that the Managed Resource Group is provisioned with Deny Assignment active.

### Step 3: Runtime Health Probes Verification
Verify operational status through App Service HTTPS endpoints:
```bash
# Test liveness probe
curl -f https://<app-name>.azurewebsites.net/healthz
# Response: {"status":"healthy","service":"hr-time-leave-agent","version":"0.1.0"}

# Test readiness probe
curl -f https://<app-name>.azurewebsites.net/readyz
# Response: {"status":"ready","service":"hr-time-leave-agent","version":"0.1.0","checks":{"domain":"ok","policy":"ok","sla":"ok"}}

# Test Bot Framework webhook endpoint
curl -X POST -H "Content-Type: application/json" -d '{"type":"message","text":"test"}' https://<app-name>.azurewebsites.net/api/messages
```

---

## 6. Microsoft IP Co-Sell Readiness Checklist

Achieving **IP Co-sell Eligible** status unlocks Microsoft field seller incentives (10-15% quota credit) and prioritized discovery in Azure Marketplace.

| Requirement | Artifact / Status | Verification |
|---|---|---|
| **Transactable Marketplace Offer** | Azure Managed Application Plan | Complete (`app.zip` packaged) |
| **Co-sell Business Solution Profile** | Completed in Partner Center Commercial Marketplace portal | Value proposition, target industries (HR, Enterprise Operations) |
| **Customer-Facing Solution Deck** | 10-slide PowerPoint presentation | Covers architecture, ROI, data privacy, and Teams UI |
| **Solution One-Pager / Fact Sheet** | 1-2 page PDF sales brief | Highlighting time savings (up to 48 hours faster approval) |
| **Reference Architecture Diagram** | Visio or Draw.io architecture topology | Azure Managed Application MRG boundary and zero-secrets security |
| **Client Case Study / Verifiable Evidence** | Customer reference or pilot deployment summary | Demonstrates business value in production environment |
