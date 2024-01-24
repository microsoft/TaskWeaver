from typing import List, Tuple

import requests

from taskweaver.plugin import Plugin, register_plugin

# response entry format: (title, url, snippet)
ResponseEntry = Tuple[str, str, str]


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

    def __call__(self, query: str) -> List[ResponseEntry]:
        return self.search_query(query)

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
