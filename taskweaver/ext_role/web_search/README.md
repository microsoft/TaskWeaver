# Bing Web Search API
https://www.microsoft.com/en-us/bing/apis/bing-web-search-api

register search resource on Azure Portal: https://aka.ms/bingapisignup
get api key from the registered resource

```json
{
    "web_search.api_provider": "bing",
    "web_search.bing_api_key": "api_key"
}
```


# Google Custom Search
https://developers.google.com/custom-search/v1/overview

get search engine id from: https://cse.google.com/all
get search api key from: https://console.cloud.google.com/apis/credentials

```json
{
    "web_search.api_provider": "google",
    "web_search.google_api_key": "api_key",
    "web_search.google_search_engine_id": "engine_id"
}
```
