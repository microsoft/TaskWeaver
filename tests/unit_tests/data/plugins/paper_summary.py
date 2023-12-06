import os

from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from langchain.document_loaders.pdf import PyPDFLoader
from langchain.schema.messages import HumanMessage, SystemMessage

from taskweaver.plugin import Plugin, register_plugin

paper_summarize_prompt = r"""
Please summarize this paper and highlight the key points, including the following:
- The problem the paper is trying to solve.
- The main idea of the paper.
- The main contributions of the paper.
- The main experiments and results of the paper.
- The main conclusions of the paper.
"""


@register_plugin
class SummarizePaperPlugin(Plugin):
    def __call__(self, paper_file_path: str):
        os.environ["OPENAI_API_TYPE"] = self.config.get("api_type", "azure")
        if os.environ["OPENAI_API_TYPE"] == "azure":
            model = AzureChatOpenAI(
                azure_endpoint=self.config.get("api_base"),
                openai_api_key=self.config.get("api_key"),
                openai_api_version=self.config.get("api_version"),
                azure_deployment=self.config.get("deployment_name"),
                temperature=0,
                verbose=True,
            )
        elif os.environ["OPENAI_API_TYPE"] == "openai":
            os.environ["OPENAI_API_KEY"] = self.config.get("api_key")
            model = ChatOpenAI(model_name=self.config.get("deployment_name"), temperature=0, verbose=True)
        else:
            raise ValueError("Invalid API type. Please check your config file.")

        loader = PyPDFLoader(paper_file_path)
        pages = loader.load()

        messages = [
            SystemMessage(content=paper_summarize_prompt),
            HumanMessage(content="The paper content:" + "\n".join([c.page_content for c in pages])),
        ]

        summary_res = model.invoke(messages).content

        description = f"We have summarized {len(pages)} pages of this paper." f"Paper summary is: {summary_res}"

        return summary_res, description
