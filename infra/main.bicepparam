using './main.bicep'

// Deployment environment targeted by this parameter file
param environmentName = 'test'

// Target Azure region for all deployed resources
param location = 'eastus2'

// Prefix for standard resource naming conventions
param appNamePrefix = 'hr-time-leave'

// Application Service Plan SKU sizing
param appServicePlanSku = 'B1'

// Azure AI Search SKU sizing
param searchSku = 'standard'

// Microsoft Teams Bot registration application ID (replace in deployment pipeline or use non-prod test ID)
param botAppId = '00000000-0000-0000-0000-000000000000'

// Optional existing Azure OpenAI endpoint; empty provisions dedicated Cognitive Services
param existingOpenAiEndpoint = ''

// Resource tags applied to all provisioned resources
param tags = {
  Project: 'Enterprise HR Time and Leave Copilot'
  Environment: 'test'
  ManagedBy: 'Bicep'
  SecurityProfile: 'LeastPrivilege-ZeroSecrets'
}
