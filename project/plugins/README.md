# Additional Information about Plugins

## klarna_search
In this plugin, we call the Klarna API to search for products.

## paper_summary
This plugin by default is **not** enabled. In this plugin, we load a pdf file (e.g., a research paper) and use Langchain to summarize the paper.
To install Langchain, you can run the following command:
```bash
pip install langchain
```

## sql_pull_data
This plugin by default is **not** enabled. In this plugin, we pull data from a sqlite database based on a query in natural language.
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
This plugin has been re-implemented as a role in the `taskweaver/ext_role/web_explorer` directory.

[Plugin Demo](https://github.com/microsoft/TaskWeaver/assets/7489260/7f819524-2c5b-46a8-9c0c-e001a2c7131b)

## web_search

This plugin has been re-implemented as a role in the `taskweaver/ext_role/web_search` directory.

A video demo using web search to find out information and then complete the task based on the retrieved information:

[Plugin Demo](https://github.com/microsoft/TaskWeaver/assets/7489260/d078a05b-a19b-498c-b712-6f8c4855cefa)


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


