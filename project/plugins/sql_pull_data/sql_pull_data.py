from operator import itemgetter

import pandas as pd
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableLambda, RunnableMap
from langchain.utilities import SQLDatabase

from taskweaver.plugin import Plugin, register_plugin


@register_plugin
class SqlPullData(Plugin):
    db = None

    def __call__(self, query: str):
        api_type = self.config.get("api_type", "azure")
        if api_type == "azure":
            model = AzureChatOpenAI(
                azure_endpoint=self.config.get("api_base"),
                openai_api_key=self.config.get("api_key"),
                openai_api_version=self.config.get("api_version"),
                azure_deployment=self.config.get("deployment_name"),
                temperature=0,
                verbose=True,
            )
        elif api_type == "openai":
            model = ChatOpenAI(
                openai_api_key=self.config.get("api_key"),
                model_name=self.config.get("deployment_name"),
                temperature=0,
                verbose=True,
            )
        else:
            raise ValueError("Invalid API type. Please check your config file.")

        template = """Based on the table schema below, write a SQL query that would answer the user's question:
            {schema}

            Question: {question}
            Please only write the sql query.
            Do not add any comments or extra text.
            Do not wrap the query in quotes or ```sql.
            SQL Query:"""
        prompt = ChatPromptTemplate.from_template(template)

        if self.db is None:
            self.db = SQLDatabase.from_uri(self.config.get("sqlite_db_path"))

        def get_schema(_):
            return self.db.get_table_info()

        inputs = {
            "schema": RunnableLambda(get_schema),
            "question": itemgetter("question"),
        }
        sql_response = RunnableMap(inputs) | prompt | model.bind(stop=["\nSQLResult:"]) | StrOutputParser()

        sql = sql_response.invoke({"question": query})

        result = self.db._execute(sql, fetch="all")

        df = pd.DataFrame(result)

        if len(df) == 0:
            return df, (
                f"I have generated a SQL query based on `{query}`.\nThe SQL query is {sql}.\n" f"The result is empty."
            )
        else:
            return df, (
                f"I have generated a SQL query based on `{query}`.\nThe SQL query is {sql}.\n"
                f"There are {len(df)} rows in the result.\n"
                f"The first {min(5, len(df))} rows are:\n{df.head(min(5, len(df))).to_markdown()}"
            )
