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

## document_retriever

This plugin by default is **not** enabled. If you want to use this plugin, you need to enable it in the `document_retriever.yaml` file.
In this plugin, we load a previously indexed document collection and retrieve the top-k documents based on a natural language query.
To use this plugin, you need to configure the path to the folder containing the index files in the plugin configuration file `document_retriever.yaml`.
A pre-built sample index is provided in the `project/sample_data/knowledge_base` folder which contains all documents for TaskWeaver under `website/docs` folder.

To build your own index, we provide a script in `script/document_indexer.py` to build the index.
You can run the following command to build the index:
```bash
python script/document_indexer.py \
  --doc_path project/sample_data/knowledge_base/website/docs \
  --output_path project/sample_data/knowledge_base/index
```
Please take a look at the import section in the script to install the required python packages.
There are two parameters `--chunk_step` and `--chunk_size` that can be specified to control the chunking of the documents.
The `--chunk_step` is the step size of the sliding window and the `--chunk_size` is the size of the sliding window.
The default values are `--chunk_step=64` and `--chunk_size=64`.
The size is measured in number of tokens and the tokenizer is based on OpenAI GPT model (i.e., `gpt-3.5-turbo`).
We intentionally split the documents with this small chunk size to make sure the chunks are small enough.
The reason is that small chunks are easier to match with the query, improving the retrieval accuracy.
Make sure you understand the consequence of changing these two parameters before you change them, for example, 
by experimenting with different values on your dataset.

The retrieval is based on FAISS. You can find more details about FAISS [here](https://ai.meta.com/tools/faiss/).
FAISS is a library for vector similarity search of dense vectors.
In our implementation, we use the wrapper class provided by Langchain to call FAISS.
The embedding of the documents and the query is based on HuggingFace's Sentence Transformers.

The retrieved document chunks are presented in the following format:
```json
{
    "chunk": "The chunk of the document",
    "metadata": {
      "source": "str, the path to the document", 
      "title": "str, the title of the document",
      "chunk_id": "integer, the id of the chunk inside the document"
    }
}
```
The title in the metadata is inferred from the file content in a heuristic way.
The chunk_id is the id of the chunk inside the document.
Neighboring chunks in the same document have consecutive chunk ids, so we can find the previous and next chunks in the same document.
In our implementation, we expand the retrieved chunks to include the previous and next chunks in the same document.
Recall that the raw chunk size is only 64 tokens, the expanded chunk size is 256 tokens by default.


