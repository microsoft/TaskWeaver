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

