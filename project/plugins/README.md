# Additional Information about Plugins

## klarna_search
In this plugin, we call the Klarna API to search for products.

## paper_summary
In this plugin, we load a pdf file (e.g., a research paper) and use Langchain to summarize the paper.
To install Langchain, you can run the following command:
```bash
pip install langchain
```

## sql_pull_data
In this plugin, we pull data from a sqlite database based on a query in natural language.
This plugin is implemented based on Langchain. So, you need to install Langchain first.
To install Langchain, you can run the following command:
```bash
pip install langchain
```
In the implementation, we first profile the database tables collecting the table names, schema, and sample data.
Then, we convert the natural language query to a SQL query. 
Finally, we use the SQL query to pull data from the sqlite database.

Because we need to generate the SQL query, we need to access GPT model. 
So, you need to configure the GPT model (similar with configuring the main project) in the plugin configuration file `sql_pull_data.yaml`.


## vision_web_explorer
This plugin by default is **not** enabled. If you want to use this plugin, you need to enable it in the `vision_web_explorer.yaml` file.
In this plugin, we use Selenium driver to open a web browser and navigate to a website. 
So, you need to install the following python packages:
```bash
pip install selenium
pip install pillow
```

We use the Chrome + ChromeDriver in this example. You can download the driver from [here](https://chromedriver.chromium.org/downloads).
Make sure you download the driver that matches your Chrome version, otherwise, the browser may crash.
For example, the latest Chrome version on 1/25/2024 is 121.0.6167.85, so you need to download the ChromeDriver 121.0.6167.85.
After downloading the driver, you need to unzip it and configure the path (i.e., `chrome_driver_path`) to the executable in the plugin configuration file `vision_web_explorer.yaml`.
If you already have Chrome installed, you can upgrade it to the latest version.
If you want to have a dedicated Chrome for this plugin, you can download the Chrome executable from [here](https://googlechromelabs.github.io/chrome-for-testing/).
After downloading the Chrome executable, you need to unzip it and configure the path to the executable (i.e., `chrome_executable_path`) in the plugin configuration file `vision_web_explorer.yaml`.
If this path is not configured, the plugin will use the default Chrome installed on your machine.


In addition, you need to configure the GPT vision model in the plugin configuration file `vision_web_explorer.yaml`.
For OpenAI GPT model, you can find the sample code [here](https://platform.openai.com/docs/guides/vision/uploading-base-64-encoded-images).
The `endpoint` is "https://api.openai.com/v1/chat/completions". 

For Azure OpenAI GPT model, you can find the manual [here](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/gpt-with-vision).
The `endpoint` is "https://{RESOURCE_NAME}.openai.azure.com/openai/deployments/{DEPLOYMENT_NAME}/chat/completions?api-version=2023-12-01-preview".
Replace {RESOURCE_NAME} and {DEPLOYMENT_NAME} with your own values.

A video demo using this plugin for web browsing:

[Plugin Demo](https://github.com/microsoft/TaskWeaver/assets/7489260/7f819524-2c5b-46a8-9c0c-e001a2c7131b)

## web_search

This plugin by default is **not** enabled. If you want to use this plugin, you need to enable it in the `web_search.yaml` file.
In this plugin, we will call the Bing Search or Google Search API to search for web pages.
The input to the plugin is a natural language query, and the output is a list of web pages including the URL, title, and a short snippet.
To use this plugin, you need to configure the API key in the plugin configuration file `web_search.yaml`.

We support two search engines: Bing Search and Google Search.

- To use Bing Search, you need to register a search resource on Azure Portal: https://aka.ms/bingapisignup.
Then, you can get the API key from the registered resource. Refer to this [link](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api) for more details.
- To use Google Search, you need to register a custom search engine on Google: https://cse.google.com/all.
Then, you can get the API key from the registered search engine from the [Credentials page](https://console.cloud.google.com/apis/credentials).
