import json
from typing import Any, List, Tuple

import requests

from taskweaver.plugin import Plugin, register_plugin

# response entry format: (title, url, snippet)
ResponseEntry = Tuple[str, str, str]


def browse_page(
    query: str,
    urls: List[str],
    top_k: int = 3,
    chunk_size: int = 1000,
    chunk_overlap: int = 250,
) -> list[dict[str, Any]]:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.document_loaders import AsyncHtmlLoader
        from langchain_community.document_transformers import Html2TextTransformer
    except ImportError:
        raise ImportError("Please install langchain/langchain-community first.")

    loader = AsyncHtmlLoader(web_path=urls)
    docs = loader.load()

    html2text = Html2TextTransformer()
    docs_transformed = html2text.transform_documents(docs)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    # Split
    splits = text_splitter.split_documents(docs_transformed)

    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS

    vector_store = FAISS.from_documents(
        splits,
        HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2"),
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


@register_plugin
class WebSearch(Plugin):
    def search_query(self, query: str) -> List[ResponseEntry]:
        api_provider = self.config.get("api_provider", "google_custom_search")
        result_count = int(self.config.get("result_count", 3))
        if api_provider == "google_custom_search":
            return self._search_google_custom_search(query, cnt=result_count)
        elif api_provider == "bing":
            return self._search_bing(query, cnt=result_count)
        else:
            raise ValueError("Invalid API provider. Please check your config file.")

    def __call__(self, queries: List[str], browse: bool = True) -> str:
        query_results = []
        query_urls = set()
        for query in queries:
            query_results.extend([r for r in self.search_query(query) if r[1] not in query_urls])
            query_urls.update([r[1] for r in query_results])

        if not browse:
            return f"WebSearch has done searching for `{queries}`.\n" + self.ctx.wrap_text_with_delimiter_temporal(
                "\n```json\n" + json.dumps(query_results, indent=4) + "```\n",
            )
        else:
            return f"WebSearch has done searching for `{queries}`.\n" + self.ctx.wrap_text_with_delimiter_temporal(
                "\n```json\n" + json.dumps(browse_page(",".join(queries), list(query_urls)), indent=4) + "```\n",
            )

    def _search_google_custom_search(self, query: str, cnt: int) -> List[ResponseEntry]:
        api_key = self.config.get("google_api_key")
        search_engine_id = self.config.get("google_search_engine_id")
        url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={search_engine_id}&q={query}"
        if cnt > 0:
            url += f"&num={cnt}"
        response = requests.get(url)
        result_list: List[ResponseEntry] = []
        for item in response.json()["items"]:
            result_list.append((item["title"], item["link"], item["snippet"]))
        return result_list

    def _search_bing(self, query: str, cnt: int) -> List[ResponseEntry]:
        api_key = self.config.get("bing_api_key")
        url = f"https://api.bing.microsoft.com/v7.0/search?q={query}"
        if cnt > 0:
            url += f"&count={cnt}"
        response = requests.get(url, headers={"Ocp-Apim-Subscription-Key": api_key})
        result_list: List[ResponseEntry] = []
        for item in response.json()["webPages"]["value"]:
            result_list.append((item["name"], item["url"], item["snippet"]))
        return result_list
