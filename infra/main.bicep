@description('The deployment environment name (dev, test, prod).')
@allowed([
  'dev'
  'test'
  'prod'
])
param environmentName string = 'dev'

@description('Azure region for all provisioned resources.')
param location string = resourceGroup().location

@description('Resource prefix used for standardized naming.')
@minLength(3)
@maxLength(16)
param appNamePrefix string = 'hr-time-leave'

@description('Microsoft Entra ID tenant ID for authentication.')
param entraTenantId string = tenant().tenantId

@description('Application / Client ID for the Microsoft Teams Bot registration.')
param botAppId string = ''

@description('SKU name for App Service Plan.')
param appServicePlanSku string = 'B1'

@description('SKU name for Azure AI Search service.')
@allowed([
  'basic'
  'standard'
])
param searchSku string = 'standard'

@description('Azure OpenAI / Foundry endpoint. If empty, a Cognitive Services OpenAI account is provisioned.')
param existingOpenAiEndpoint string = ''

@description('Container image repository and tag for the HR Copilot App Service.')
param containerImage string = 'ghcr.io/zerosaber10-dev/hr-time-leave-agent:latest'

@description('Tags to apply to all resources.')
param tags object = {
  Project: 'Enterprise HR Time and Leave Copilot'
  Environment: environmentName
  ManagedBy: 'Bicep'
  SecurityProfile: 'LeastPrivilege-ZeroSecrets'
}

// ---------------------------------------------------------------------------
// Variables: Unique deterministic resource naming
// ---------------------------------------------------------------------------
var uniqueSuffix = uniqueString(resourceGroup().id)
var cleanPrefix = toLower(replace(appNamePrefix, '-', ''))
var effectiveEntraTenantId = empty(entraTenantId) ? tenant().tenantId : entraTenantId

var names = {
  logAnalytics: '${appNamePrefix}-${environmentName}-log-${uniqueSuffix}'
  appInsights: '${appNamePrefix}-${environmentName}-appi-${uniqueSuffix}'
  storageAccount: take('${cleanPrefix}${environmentName}st${uniqueSuffix}', 24)
  keyVault: take('${appNamePrefix}-${environmentName}-kv-${uniqueSuffix}', 24)
  cosmosAccount: '${appNamePrefix}-${environmentName}-cosmos-${uniqueSuffix}'
  searchService: '${appNamePrefix}-${environmentName}-search-${uniqueSuffix}'
  serviceBusNamespace: '${appNamePrefix}-${environmentName}-sb-${uniqueSuffix}'
  appServicePlan: '${appNamePrefix}-${environmentName}-asp-${uniqueSuffix}'
  appService: '${appNamePrefix}-${environmentName}-app-${uniqueSuffix}'
  functionApp: '${appNamePrefix}-${environmentName}-func-${uniqueSuffix}'
  cognitiveService: '${appNamePrefix}-${environmentName}-ai-${uniqueSuffix}'
  botService: '${appNamePrefix}-${environmentName}-bot-${uniqueSuffix}'
}

// Built-in Azure RBAC Role Definition IDs
var roleDefinitionIds = {
  keyVaultSecretsUser: '4633458b-17de-408a-b874-0445c86b69e6'
  serviceBusDataSender: '69a216fc-b8fb-44d8-bc22-f94f7c3b9d50'
  serviceBusDataReceiver: '4f6d3a01-b295-46f1-a042-a3c6130c67b3'
  searchIndexDataContributor: '8ebe5a5f-32e7-4f83-8015-3ea22f308c37'
  searchServiceContributor: '7ca78c08-252a-4471-8641-05f40b2244eb'
  cognitiveServicesOpenAiUser: '5e070246-6308-41f1-a775-92a59d4f2d70'
  storageBlobDataReader: '2a2b9908-6ea1-4836-8bb7-5265d162ba8e'
  storageBlobDataOwner: 'b7e6dc6d-f1e8-4753-8033-08440cdcdd80'
}

// Built-in Cosmos DB SQL Data Contributor Role ID
var cosmosDataContributorRoleId = '00000000-0000-0000-0000-000000000002'

// ---------------------------------------------------------------------------
// 1. Observability: Log Analytics Workspace & Application Insights (NFR-001, NFR-012, NFR-014)
// ---------------------------------------------------------------------------
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: names.logAnalytics
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 90
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: names.appInsights
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    RetentionInDays: 90
    DisableLocalAuth: true
  }
}

// ---------------------------------------------------------------------------
// 2. Storage Account: Policy Document Repository & Functions Runtime (ADR-0001)
// ---------------------------------------------------------------------------
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: names.storageAccount
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
  }
}

resource blobServices 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 30
    }
  }
}

resource policyDocumentsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobServices
  name: 'policy-documents'
  properties: {
    publicAccess: 'None'
  }
}

resource functionsDeploymentContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobServices
  name: 'functions-deployment'
  properties: {
    publicAccess: 'None'
  }
}

// ---------------------------------------------------------------------------
// 3. Azure Key Vault: Central Secret Store with Azure RBAC (Zero hardcoded secrets)
// ---------------------------------------------------------------------------
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: names.keyVault
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: effectiveEntraTenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
  }
}

// ---------------------------------------------------------------------------
// 4. Azure Cosmos DB: Separate Ticket & Memory Databases (ADR-0001, NFR-013)
// ---------------------------------------------------------------------------
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: names.cosmosAccount
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    disableKeyBasedMetadataWriteAccess: true
    disableLocalAuth: true
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
  }
}

// Database 1: Ticket Store & Attributable Audit Log
resource ticketDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmosAccount
  name: 'hr-ticket-store'
  properties: {
    resource: {
      id: 'hr-ticket-store'
    }
  }
}

resource ticketsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: ticketDatabase
  name: 'tickets'
  properties: {
    resource: {
      id: 'tickets'
      partitionKey: {
        paths: [
          '/ticket_id'
        ]
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/medical_notes/*'
          }
          {
            path: '/medical_reason/*'
          }
          {
            path: '/overtime_calculation_details/*'
          }
        ]
      }
    }
  }
}

// Database 2: Isolated Conversation Memory (LangGraph Checkpoints)
resource memoryDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmosAccount
  name: 'hr-conversation-memory'
  properties: {
    resource: {
      id: 'hr-conversation-memory'
    }
  }
}

resource memoryContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: memoryDatabase
  name: 'sessions'
  properties: {
    resource: {
      id: 'sessions'
      partitionKey: {
        paths: [
          '/user_id'
        ]
        kind: 'Hash'
      }
      defaultTtl: 2592000 // 30 days session retention
    }
  }
}

// ---------------------------------------------------------------------------
// 5. Azure AI Search: BM25 + Vector + Semantic Reranking (FR-001, ADR-0001)
// ---------------------------------------------------------------------------
resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: names.searchService
  location: location
  tags: tags
  sku: {
    name: searchSku
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    semanticSearch: 'free'
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
}

// ---------------------------------------------------------------------------
// 6. Azure Service Bus: Asynchronous SLA Timers & Escalations (FR-004, NFR-002, NFR-004)
// ---------------------------------------------------------------------------
resource serviceBusNamespace 'Microsoft.ServiceBus/namespaces@2021-11-01' = {
  name: names.serviceBusNamespace
  location: location
  tags: tags
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {
    disableLocalAuth: true
  }
}

resource slaQueue 'Microsoft.ServiceBus/namespaces/queues@2021-11-01' = {
  parent: serviceBusNamespace
  name: 'hr-sla-jobs'
  properties: {
    requiresDuplicateDetection: true
    duplicateDetectionHistoryTimeWindow: 'PT10M'
    deadLetteringOnMessageExpiration: true
    maxDeliveryCount: 5
    defaultMessageTimeToLive: 'P14D'
    enableBatchedOperations: true
  }
}

// ---------------------------------------------------------------------------
// 7. Azure AI Foundry / Cognitive Services (Grounded Policy Q&A Model & Embeddings)
// ---------------------------------------------------------------------------
resource cognitiveService 'Microsoft.CognitiveServices/accounts@2024-10-01' = if (empty(existingOpenAiEndpoint)) {
  name: names.cognitiveService
  location: location
  tags: tags
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: toLower(names.cognitiveService)
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true
  }
}

resource gptDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = if (empty(existingOpenAiEndpoint)) {
  parent: cognitiveService
  name: 'gpt-6-luna'
  sku: {
    name: 'GlobalStandard'
    capacity: 20
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-6-luna'
      version: '2026-09-22'
    }
  }
}

resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = if (empty(existingOpenAiEndpoint)) {
  parent: cognitiveService
  name: 'text-embedding-3-small'
  sku: {
    name: 'Standard'
    capacity: 20
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-small'
      version: '1'
    }
  }
}

var openAiResolvedEndpoint = empty(existingOpenAiEndpoint) ? 'https://${toLower(names.cognitiveService)}.cognitiveservices.azure.com/' : existingOpenAiEndpoint

// ---------------------------------------------------------------------------
// 8. Azure App Service: LangGraph State Machine & Internal MCP Hosting (ADR-0001)
// ---------------------------------------------------------------------------
resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: names.appServicePlan
  location: location
  tags: tags
  sku: {
    name: appServicePlanSku
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

resource appService 'Microsoft.Web/sites@2023-12-01' = {
  name: names.appService
  location: location
  tags: tags
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'DOCKER|${containerImage}'
      alwaysOn: (appServicePlanSku != 'F1' && appServicePlanSku != 'D1')
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: [
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'AZURE_CLIENT_ID'
          value: ''
        }
        {
          name: 'AZURE_TENANT_ID'
          value: effectiveEntraTenantId
        }
        {
          name: 'COSMOS_DB_ENDPOINT'
          value: cosmosAccount.properties.documentEndpoint
        }
        {
          name: 'COSMOS_TICKET_DATABASE'
          value: ticketDatabase.name
        }
        {
          name: 'COSMOS_MEMORY_DATABASE'
          value: memoryDatabase.name
        }
        {
          name: 'AI_SEARCH_ENDPOINT'
          value: 'https://${searchService.name}.search.windows.net'
        }
        {
          name: 'SERVICE_BUS_NAMESPACE'
          value: '${serviceBusNamespace.name}.servicebus.windows.net'
        }
        {
          name: 'SERVICE_BUS_QUEUE'
          value: slaQueue.name
        }
        {
          name: 'KEY_VAULT_URI'
          value: keyVault.properties.vaultUri
        }
        {
          name: 'OPENAI_ENDPOINT'
          value: openAiResolvedEndpoint
        }
        {
          name: 'OPENAI_DEPLOYMENT_NAME'
          value: 'gpt-6-luna'
        }
        {
          name: 'STORAGE_ACCOUNT_BLOB_URL'
          value: storageAccount.properties.primaryEndpoints.blob
        }
        {
          name: 'BOT_APP_ID'
          value: botAppId
        }
        {
          name: 'WEBSITES_PORT'
          value: '8000'
        }
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'WEBSITES_CONTAINER_START_TIME_LIMIT'
          value: '600'
        }
      ]
    }
  }
}

// ---------------------------------------------------------------------------
// 9. Azure Functions: Asynchronous SLA Reminder & Escalation Handlers (FR-004)
// ---------------------------------------------------------------------------
resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: names.functionApp
  location: location
  tags: tags
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      alwaysOn: (appServicePlanSku != 'F1' && appServicePlanSku != 'D1')
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: [
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'AzureWebJobsStorage__accountName'
          value: storageAccount.name
        }
        {
          name: 'SERVICE_BUS_CONNECTION__fullyQualifiedNamespace'
          value: '${serviceBusNamespace.name}.servicebus.windows.net'
        }
        {
          name: 'COSMOS_DB_ENDPOINT'
          value: cosmosAccount.properties.documentEndpoint
        }
        {
          name: 'COSMOS_TICKET_DATABASE'
          value: ticketDatabase.name
        }
        {
          name: 'KEY_VAULT_URI'
          value: keyVault.properties.vaultUri
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
      ]
    }
  }
}

// ---------------------------------------------------------------------------
// 10. Azure Bot Service & Microsoft Teams Channel Integration (FR-003)
// ---------------------------------------------------------------------------
resource botService 'Microsoft.BotService/botServices@2022-09-15' = if (!empty(botAppId)) {
  name: names.botService
  location: 'global'
  tags: tags
  sku: {
    name: 'F0'
  }
  kind: 'azurebot'
  properties: {
    displayName: 'Enterprise HR Time and Leave Copilot'
    endpoint: 'https://${appService.properties.defaultHostName}/api/messages'
    msaAppId: botAppId
    msaAppType: 'SingleTenant'
    msaAppTenantId: effectiveEntraTenantId
    disableLocalAuth: true
  }
}

resource teamsChannel 'Microsoft.BotService/botServices/channels@2022-09-15' = if (!empty(botAppId)) {
  parent: botService
  name: 'MsTeamsChannel'
  location: 'global'
  properties: {
    channelName: 'MsTeamsChannel'
    properties: {
      isEnabled: true
    }
  }
}

// ---------------------------------------------------------------------------
// 11. Least-Privilege RBAC Assignments (Zero Hardcoded Secrets / Credentials)
// ---------------------------------------------------------------------------

// App Service -> Key Vault Secrets User
resource appKeyVaultRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, appService.id, roleDefinitionIds.keyVaultSecretsUser)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionIds.keyVaultSecretsUser)
    principalId: appService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Function App -> Key Vault Secrets User
resource funcKeyVaultRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, functionApp.id, roleDefinitionIds.keyVaultSecretsUser)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionIds.keyVaultSecretsUser)
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// App Service -> Service Bus Data Sender
resource appServiceBusSenderRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(serviceBusNamespace.id, appService.id, roleDefinitionIds.serviceBusDataSender)
  scope: serviceBusNamespace
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionIds.serviceBusDataSender)
    principalId: appService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Function App -> Service Bus Data Receiver
resource funcServiceBusReceiverRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(serviceBusNamespace.id, functionApp.id, roleDefinitionIds.serviceBusDataReceiver)
  scope: serviceBusNamespace
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionIds.serviceBusDataReceiver)
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// App Service -> Azure AI Search Index Data Contributor
resource appSearchDataRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, appService.id, roleDefinitionIds.searchIndexDataContributor)
  scope: searchService
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionIds.searchIndexDataContributor)
    principalId: appService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// App Service -> Azure Cognitive Services OpenAI User
resource appCognitiveRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (empty(existingOpenAiEndpoint)) {
  name: guid(cognitiveService.id, appService.id, roleDefinitionIds.cognitiveServicesOpenAiUser)
  scope: cognitiveService
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionIds.cognitiveServicesOpenAiUser)
    principalId: appService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// App Service -> Storage Blob Data Reader (Policy Documents)
resource appStorageReaderRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, appService.id, roleDefinitionIds.storageBlobDataReader)
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionIds.storageBlobDataReader)
    principalId: appService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Function App -> Storage Blob Data Owner (Functions Runtime State)
resource funcStorageOwnerRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, functionApp.id, roleDefinitionIds.storageBlobDataOwner)
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionIds.storageBlobDataOwner)
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Cosmos DB SQL Role Assignment: App Service -> Built-in Data Contributor
resource appCosmosRole 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = {
  parent: cosmosAccount
  name: guid(cosmosAccount.id, appService.id, cosmosDataContributorRoleId)
  properties: {
    roleDefinitionId: resourceId('Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions', cosmosAccount.name, cosmosDataContributorRoleId)
    principalId: appService.identity.principalId
    scope: cosmosAccount.id
  }
}

// Cosmos DB SQL Role Assignment: Function App -> Built-in Data Contributor
resource funcCosmosRole 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = {
  parent: cosmosAccount
  name: guid(cosmosAccount.id, functionApp.id, cosmosDataContributorRoleId)
  properties: {
    roleDefinitionId: resourceId('Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions', cosmosAccount.name, cosmosDataContributorRoleId)
    principalId: functionApp.identity.principalId
    scope: cosmosAccount.id
  }
}

// ---------------------------------------------------------------------------
// Outputs: Non-sensitive deployment endpoints
// ---------------------------------------------------------------------------
@description('Primary HTTPS endpoint of the HR Copilot App Service.')
output appServiceEndpoint string = 'https://${appService.properties.defaultHostName}'

@description('Primary HTTPS endpoint of the SLA Function App.')
output functionAppEndpoint string = 'https://${functionApp.properties.defaultHostName}'

@description('Azure Cosmos DB document endpoint.')
output cosmosDbEndpoint string = cosmosAccount.properties.documentEndpoint

@description('Azure AI Search service endpoint.')
output aiSearchEndpoint string = 'https://${searchService.name}.search.windows.net'

@description('Azure Service Bus namespace fully qualified domain name.')
output serviceBusEndpoint string = '${serviceBusNamespace.name}.servicebus.windows.net'

@description('Azure Key Vault URI.')
output keyVaultUri string = keyVault.properties.vaultUri

@description('Resolved Azure OpenAI / Foundry endpoint.')
output openAiEndpoint string = openAiResolvedEndpoint

@description('Resource names dictionary for operational reference.')
output resourceNames object = {
  appService: appService.name
  functionApp: functionApp.name
  cosmosAccount: cosmosAccount.name
  searchService: searchService.name
  serviceBusNamespace: serviceBusNamespace.name
  keyVault: keyVault.name
  storageAccount: storageAccount.name
}
