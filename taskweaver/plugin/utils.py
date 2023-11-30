# This is used to define common functions/tools that could be used by different plugins
from __future__ import annotations

import json
from typing import Any, Dict, Union
from urllib.parse import urljoin

import requests


def make_api_call(
    host: Any = "",
    endpoint: Any = "",
    method: Any = "GET",
    headers: Dict[str, str] = {"Content-Type": "application/json"},
    query_params: Union[Dict[str, Any], str, Any] = {},
    body: str = "",
    timeout_secs: int = 60,
) -> str:
    """Make an API call to a given host and endpoint"""
    response = {}
    if not (isinstance(host, str) and isinstance(endpoint, str) and isinstance(method, str)):
        raise ValueError("host, endpoint, method, and body must be a string")

    allowed_methods = ["GET", "POST", "PUT", "DELETE"]
    if method not in allowed_methods:
        raise ValueError(f"method must be one of {allowed_methods}")

    if not query_params:
        query_params = {}
    elif isinstance(query_params, str):
        try:
            query_params = json.loads(query_params)
        except json.JSONDecodeError:
            raise ValueError(
                "query_params must be a dictionary or a JSON string",
            )
    elif not isinstance(query_params, dict):
        raise ValueError("query_params must be a dictionary or a JSON string")

    if not host.startswith(("http://", "https://")):
        normalized_host: str = f"https://{host}"
    else:
        normalized_host = host

    url = urljoin(normalized_host, endpoint)

    try:
        if method not in allowed_methods:
            raise ValueError(f"method must be one of {allowed_methods}")
        response = requests.request(method=method, url=url, headers=headers, json=body, timeout=timeout_secs)

        response_text = response.text
        response = {
            "status": "success",
            "status_code": response.status_code,
            "response": response_text,
        }
    except requests.exceptions.RequestException as e:
        response = {
            "status": "error",
            "status_code": 500,
            "response": str(e),
        }
    return json.dumps(response)
