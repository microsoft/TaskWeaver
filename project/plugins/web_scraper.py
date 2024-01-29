from typing import List, Tuple
import requests
from taskweaver.plugin import Plugin, register_plugin
from bs4 import BeautifulSoup
import re
import markdownify
import io
import pdfminer.high_level
import os
from urllib.parse import urlparse
from pathvalidate import sanitize_filename

# Response entry format: (title, url, snippet)
ResponseEntry = Tuple[str, str, str]

@register_plugin
class WebSearch(Plugin):
    def __init__(self, config: dict):
        super().__init__(config)
        self.scraper_enabled = self.config.get("scraper_enabled", False)

    def search_query(self, query: str) -> List[ResponseEntry]:
        provider = self.config.get("provider", "bing")
        result_count = int(self.config.get("result_count", 3))
        if provider == "google":
            return self._search_google_custom_search(query, cnt=result_count)
        elif provider == "bing":
            return self._search_bing(query, cnt=result_count)
        elif provider == "duckduckgo":
            return self._search_duckduckgo(query, cnt=result_count)
        else:
            raise ValueError("Invalid API provider. Please check your config file.")

    def __call__(self, query: str) -> List[ResponseEntry]:
        return self.search_query(query)

    def _fetch_page(self, url: str) -> str:
        if not self.scraper_enabled:
            return ""  # Return empty string if scraper is disabled
        try:
            # Prepare the request parameters
            request_kwargs = self.request_kwargs.copy() if self.request_kwargs is not None else {}
            request_kwargs["stream"] = True

            # Send a HTTP request to the URL
            response = requests.get(url, **request_kwargs)
            response.raise_for_status()

            # If the HTTP request returns a status code 200, proceed
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                for ct in ["text/html", "text/plain", "application/pdf"]:
                    if ct in content_type.lower():
                        content_type = ct
                        break

                if content_type == "text/html":
                    # Get the content of the response
                    html = ""
                    for chunk in response.iter_content(chunk_size=512, decode_unicode=True):
                        html += chunk

                    soup = BeautifulSoup(html, "html.parser")

                    # Remove javascript and style blocks
                    for script in soup(["script", "style"]):
                        script.extract()

                    # Convert to markdown -- Wikipedia gets special attention to get a clean version of the page
                    if url.startswith("https://en.wikipedia.org/"):
                        body_elm = soup.find("div", {"id": "mw-content-text"})
                        title_elm = soup.find("span", {"class": "mw-page-title-main"})

                        if body_elm:
                            # What's the title
                            main_title = soup.title.string
                            if title_elm and len(title_elm) > 0:
                                main_title = title_elm.string
                            webpage_text = (
                                "# " + main_title + "\n\n" + markdownify.markdownify(str(body_elm))
                            )
                        else:
                            webpage_text = markdownify.markdownify(str(soup))
                    else:
                        webpage_text = markdownify.markdownify(str(soup))

                    # Convert newlines
                    webpage_text = re.sub(r"\r\n", "\n", webpage_text)

                    # Remove excessive blank lines
                    return re.sub(r"\n{2,}", "\n\n", webpage_text).strip()
                elif content_type == "text/plain":
                    # Get the content of the response
                    plain_text = ""
                    for chunk in response.iter_content(chunk_size=512, decode_unicode=True):
                        plain_text += chunk
                    return plain_text
                elif self.scraper_enabled and content_type == "application/pdf":
                    pdf_data = io.BytesIO(response.content)
                    return pdfminer.high_level.extract_text(pdf_data)
        except Exception as e:
            # Handle any exceptions
            print(f"Error fetching page: {e}")
        return ""

    def _search_google_custom_search(self, query: str, cnt: int) -> List[ResponseEntry]:
        api_key = self.config.get("google_api_key")
        search_engine_id = self.config.get("google_search_engine_id")
        url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={search_engine_id}&q={query}"
        if cnt > 0:
            url += f"&num={cnt}"
        response = requests.get(url)
        result_list: List[ResponseEntry] = []
        for item in response.json()["items"]:
            title = item["title"]
            url = item["link"]
            snippet = self._fetch_page(url)
            result_list.append((title, url, snippet))
        return result_list

    def _search_bing(self, query: str, cnt: int) -> List[ResponseEntry]:
        api_key = self.config.get("bing_api_key")
        url = f"https://api.bing.microsoft.com/v7.0/search?q={query}"
        if cnt > 0:
            url += f"&count={cnt}"
        response = requests.get(url, headers={"Ocp-Apim-Subscription-Key": api_key})
        result_list: List[ResponseEntry] = []
        for item in response.json()["webPages"]["value"]:
            title = item["name"]
            url = item["url"]
            snippet = self._fetch_page(url)
            result_list.append((title, url, snippet))
        return result_list

    def _search_duckduckgo(self, query: str, cnt: int) -> List[ResponseEntry]:
        url = f"https://api.duckduckgo.com/?q={query}&format=json"
        response = requests.get(url)
        result_list: List[ResponseEntry] = []
        for item in response.json()["RelatedTopics"]:
            title = item["Text"]
            url = item["FirstURL"]
            snippet = self._fetch_page(url)
            result_list.append((title, url, snippet))
        return result_list
