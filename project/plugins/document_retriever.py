from taskweaver.plugin import Plugin, register_plugin


@register_plugin
class DocumentRetriever(Plugin):
    vectorstore = None

    def _init(self):
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            from langchain_community.vectorstores import FAISS
        except ImportError:
            raise ImportError("Please install langchain-community first.")

        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vectorstore = FAISS.load_local(
            folder_path=self.config.get("index_folder"),
            embeddings=self.embeddings,
        )

    def __call__(self, query: str, size: int = 5):
        if self.vectorstore is None:
            self._init()

        result = self.vectorstore.similarity_search(
            query=query,
            k=size,
        )

        return [
            {
                "chunk": r.page_content,
                "metadata": r.metadata,
            }
            for r in result
        ]
