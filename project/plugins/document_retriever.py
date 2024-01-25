from taskweaver.plugin import Plugin, register_plugin


@register_plugin
class DocumentRetriever(Plugin):
    def __call__(self, query: str, size: int = 3):
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            from langchain_community.vectorstores import FAISS
        except ImportError:
            raise ImportError("Please install langchain-community first.")

        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = FAISS.load_local(
            folder_path=self.config.get("index_folder"),
            embeddings=embeddings,
        )

        result = vectorstore.similarity_search(
            query=query,
            k=size,
        )

        return [{"chunk": r.page_content, "metadata": r.metadata} for r in result]
