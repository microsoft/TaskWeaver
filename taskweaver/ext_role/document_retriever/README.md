In this role, we load a previously indexed document collection and retrieve the top-k documents based on a natural language query.
To enable this role, you need to configure the path to the folder containing the index files in the project configuration file `project/taskweaver_config.json`.
In addition, you need to add `document_retriever` to the `session.roles` list in the project configuration file `project/taskweaver_config.json`.
A pre-built sample index is provided which contains all documents for TaskWeaver under `project/sample_data/knowledge_base` folder.
So, an example configuration is as follows:
```json
{
  "session.roles": ["document_retriever", "planner", "code_interpreter"],
  "document_retriever.index_folder": "/path/to/TaskWeaver/project/sample_data/knowledge_base"
}
```

To build your own index, we provide a script in `script/document_indexer.py` to build the index.
You can run the following command to build the index:
```bash
cd TaskWeaver
python script/document_indexer.py \
  --doc_paths website/docs website/blog \
  --output_path project/sample_data/knowledge_base \
  --extensions md
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

