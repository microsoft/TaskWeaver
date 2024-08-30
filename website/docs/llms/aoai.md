---
description: Using LLMs from OpenAI/AOAI
---
# Azure OpenAI

## Using API Key

1. Create an account on [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) and get your API key.
2. Create a new deployment of the model and get the deployment name.
3. Add the following to your `taskweaver_config.json` file:
```jsonc showLineNumbers
{
  "llm.api_base":"YOUR_AOAI_ENDPOINT", // in the format of https://<my-resource>.openai.azure.com"
  "llm.api_key":"YOUR_API_KEY",
  "llm.api_type":"azure",
  "llm.auth_mode":"api-key",
  "llm.model":"gpt-4-1106-preview", // this is known as deployment_name in Azure OpenAI
  "llm.response_format": "json_object"
}
```

:::info
For model versions or after `1106`, `llm.response_format` can be set to `json_object`.
However, for the earlier models, which do not support JSON response explicitly, `llm.response_format` should be set to `null`.
:::

4. Start TaskWeaver and chat with TaskWeaver.
You can refer to the [Quick Start](../quickstart.md) for more details.

## Using Entra Authentication

1. Create an account on [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) and 
   [assign the proper Azure RBAC Role](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/role-based-access-control) to your account (or service principal).
2. Create a new deployment of the model and get the deployment name.
3. Add the following to your `taskweaver_config.json` file:
  ```jsonc showLineNumbers
  {
    "llm.api_base":"YOUR_AOAI_ENDPOINT", // in the format of https://<my-resource>.openai.azure.com"
    "llm.api_type":"azure_ad",
    "llm.auth_mode":"default_azure_credential",
    "llm.model":"gpt-4-1106-preview", // this is known as deployment_name in Azure OpenAI
    "llm.response_format": "json_object"
  }
  ```
4. Install extra dependencies:
   ```bash
   pip install azure-identity
   ```
5. Optionally configure additional environment variables or dependencies for the specifying authentication method:
   
   Internally, authentication is handled by the `DefaultAzureCredential` class from the `azure-identity` package. It would try to authenticate using a series of methods depending on the availability in current running environment (such as environment variables, managed identity, etc.). You can refer to the [official documentation](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential?view=azure-python) for more details.

   For example, you can specify different environment variables to control the authentication method:
   1. Authenticating with AzureCLI (recommended for local development):
      
      Install AzureCLI and ensure `az` is available in your PATH. Then run the following command to login:
      ```bash
      az login
      ```
   
   2. Authenticating with Managed Identity (recommended for Azure environment):
      
      If you are running TaskWeaver on Azure, you can use Managed Identity for authentication. You can check the document for specific Azure services on how to enable Managed Identity.

      When using user assigned managed identity, you can set the following environment variable to specify the client ID of the managed identity:
      ```bash
      export AZURE_CLIENT_ID="YOUR_CLIENT_ID"
      ```
   
   3. Authenticating with Service Principal:

      You can follow the docs in the [official documentation](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.environmentcredential?view=azure-python) to specify the environment variables for Service Principal authentication.
      
6. Start TaskWeaver and chat with TaskWeaver.