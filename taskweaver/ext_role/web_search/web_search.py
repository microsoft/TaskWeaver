import json
import os
import sys
from contextlib import contextmanager
from typing import Any, List, Tuple

from injector import inject

from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Memory, Post
from taskweaver.memory.attachment import AttachmentType
from taskweaver.module.event_emitter import PostEventProxy, SessionEventEmitter
from taskweaver.module.prompt_util import PromptUtil
from taskweaver.module.tracing import Tracing
from taskweaver.role import Role
from taskweaver.role.role import RoleConfig, RoleEntry

# response entry format: (title, url, snippet)
ResponseEntry = Tuple[str, str, str]


def asyncio_suppress():
    # suppress asyncio runtime warning
    if sys.platform == "win32":
        import asyncio

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@contextmanager
def disable_tqdm():
    # Save the original value of the TQDM_DISABLE environment variable
    original_tqdm_disable = os.environ.get("TQDM_DISABLE", None)

    # Set TQDM_DISABLE to 'True' to disable tqdm
    os.environ["TQDM_DISABLE"] = "True"

    try:
        yield
    finally:
        # Restore the original TQDM_DISABLE value
        if original_tqdm_disable is None:
            del os.environ["TQDM_DISABLE"]
        else:
            os.environ["TQDM_DISABLE"] = original_tqdm_disable


def browse_page(
    query: str,
    urls: List[str],
    top_k: int = 3,
    chunk_size: int = 2000,
    chunk_overlap: int = 250,
    post_proxy: PostEventProxy = None,
) -> list[dict[str, Any]]:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.document_loaders import AsyncHtmlLoader
        from langchain_community.document_transformers import Html2TextTransformer
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_community.vectorstores import FAISS
    except ImportError:
        raise ImportError(
            """Please install the following packages first:
               pip install duckduckgo_search>=5.1.0
               pip install langchain>=0.1.4
               pip install langchain-community>=0.0.16
               pip install beautifulsoup4>=4.12.2
               pip install html2text>=2020.1.16
               pip install faiss-cpu>=1.8.0
               pip install sentence-transformers>=2.6.0
            """,
        )

    post_proxy.update_attachment(
        message="WebSearch is loading the pages...",
        type=AttachmentType.text,
    )

    loader = AsyncHtmlLoader(web_path=urls, ignore_load_errors=True)
    with disable_tqdm():
        docs = loader.load()

    post_proxy.update_attachment(
        message="WebSearch is transforming the pages...",
        type=AttachmentType.text,
    )
    html2text = Html2TextTransformer()
    docs_transformed = html2text.transform_documents(docs)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    # Split
    splits = text_splitter.split_documents(docs_transformed)

    post_proxy.update_attachment(
        message="WebSearch is indexing the pages...",
        type=AttachmentType.text,
    )
    vector_store = FAISS.from_documents(
        splits,
        HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2"),
    )

    post_proxy.update_attachment(
        message=f"WebSearch is querying the pages on {query}...",
        type=AttachmentType.text,
    )
    result = vector_store.similarity_search(
        query=query,
        k=top_k,
    )

    chunks = [
        {
            "metadata": r.metadata,
            "snippet": r.page_content,
        }
        for r in result
    ]

    return chunks


class WebSearchConfig(RoleConfig):
    def _configure(self):
        self.api_provider = self._get_str("api_provider", "duckduckgo")
        self.result_count = self._get_int("result_count", 3)
        self.google_api_key = self._get_str("google_api_key", "")
        self.google_search_engine_id = self._get_str("google_search_engine_id", "")
        self.bing_api_key = self._get_str("bing_api_key", "")
        self.chunk_size = self._get_int("chunk_size", 2000)
        self.chunk_overlap = self._get_int("chunk_overlap", 500)


class WebSearch(Role):
    @inject
    def __init__(
        self,
        config: WebSearchConfig,
        logger: TelemetryLogger,
        tracing: Tracing,
        event_emitter: SessionEventEmitter,
        role_entry: RoleEntry,
    ):
        super().__init__(config, logger, tracing, event_emitter, role_entry)

        asyncio_suppress()

        self.api_provider = config.api_provider
        self.result_count = config.result_count
        self.google_api_key = config.google_api_key
        self.google_search_engine_id = config.google_search_engine_id
        self.bing_api_key = config.bing_api_key
        self.chunk_size = config.chunk_size
        self.chunk_overlap = config.chunk_overlap

    def close(self) -> None:
        super().close()

    def search_query(self, query: str) -> List[ResponseEntry]:
        if self.api_provider == "google":
            return self._search_google_custom_search(query, cnt=self.result_count)
        elif self.api_provider == "bing":
            return self._search_bing(query, cnt=self.result_count)
        elif self.api_provider == "duckduckgo":
            return self._search_duckduckgo(query, cnt=self.result_count)
        else:
            raise ValueError("Invalid API provider. Please check your config file.")

    def reply(self, memory: Memory, **kwargs) -> Post:
        rounds = memory.get_role_rounds(
            role=self.alias,
            include_failure_rounds=False,
        )
        last_post = rounds[-1].post_list[-1]
        post_proxy = self.event_emitter.create_post_proxy(self.alias)
        post_proxy.update_send_to(last_post.send_from)

        message = last_post.message
        if "|" in message:
            queries = message.split("|")
        else:
            queries = [message]

        query_results = []
        query_urls = set()
        for query in queries:
            query_results.extend([r for r in self.search_query(query) if r[1] not in query_urls])
            query_urls.update([r[1] for r in query_results])

        post_proxy.update_message(
            f"WebSearch has done searching for `{queries}`.\n"
            + PromptUtil.wrap_text_with_delimiter(
                "\n```json\n"
                + json.dumps(
                    browse_page(
                        ",".join(queries),
                        list(query_urls),
                        post_proxy=post_proxy,
                        chunk_size=self.chunk_size,
                        chunk_overlap=self.chunk_overlap,
                    ),
                    indent=4,
                )
                + "```\n",
                PromptUtil.DELIMITER_TEMPORAL,
            ),
        )

        return post_proxy.end()

    def _search_google_custom_search(self, query: str, cnt: int) -> List[ResponseEntry]:
        import requests

        url = (
            f"https://www.googleapis.com/customsearch/v1?key={self.google_api_key}&"
            f"cx={self.google_search_engine_id}&q={query}"
        )
        if cnt > 0:
            url += f"&num={cnt}"
        response = requests.get(url)
        result_list: List[ResponseEntry] = []
        for item in response.json()["items"]:
            result_list.append((item["title"], item["link"], item["snippet"]))
        return result_list

    def _search_bing(self, query: str, cnt: int) -> List[ResponseEntry]:
        import requests

        url = f"https://api.bing.microsoft.com/v7.0/search?q={query}"
        if cnt > 0:
            url += f"&count={cnt}"
        response = requests.get(url, headers={"Ocp-Apim-Subscription-Key": self.bing_api_key})
        result_list: List[ResponseEntry] = []
        for item in response.json()["webPages"]["value"]:
            result_list.append((item["name"], item["url"], item["snippet"]))
        return result_list

    @staticmethod
    def _search_duckduckgo(query: str, cnt: int) -> List[ResponseEntry]:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            raise ImportError("Please install duckduckgo-search first.")

        results = DDGS().text(keywords=query, max_results=cnt)
        result_list: List[ResponseEntry] = []
        for result in results:
            result_list.append((result["title"], result["href"], result["body"]))
        return result_list
