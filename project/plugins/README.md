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

We use the Chrome driver in this example. You can download the driver from [here](https://chromedriver.chromium.org/downloads). 
We tested the plugin with Chrome version >= 120.
After downloading the driver, you need to unzip it and configure the path to the executable in the plugin configuration file `vision_web_explorer.yaml`.
Also, you need to install Chrome browser on your machine.

In addition, you need to configure the GPT vision model in the plugin configuration file `vision_web_explorer.yaml`.
For OpenAI GPT model, you can find the sample code [here](https://platform.openai.com/docs/guides/vision/uploading-base-64-encoded-images).
The `endpoint` is "https://api.openai.com/v1/chat/completions". 

For Azure OpenAI GPT model, you can find the manual [here](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/gpt-with-vision).
The `endpoint` is "https://{RESOURCE_NAME}.openai.azure.com/openai/deployments/{DEPLOYMENT_NAME}/chat/completions?api-version=2023-12-01-preview".
Replace {RESOURCE_NAME} and {DEPLOYMENT_NAME} with your own values.

