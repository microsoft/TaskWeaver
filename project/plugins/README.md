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

This plugin has been re-implemented as a role in the `taskweaver/ext_role/document_retriever` directory.
