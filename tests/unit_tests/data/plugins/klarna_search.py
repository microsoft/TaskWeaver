import pandas as pd
import requests

from taskweaver.plugin import Plugin, register_plugin, test_plugin


@register_plugin
class APICaller(Plugin):
    def __call__(self, query: str, size: int = 5, min_price: int = 0, max_price: int = 1000000):
        # Define the API endpoint and parameters
        base_url = "https://www.klarna.com/us/shopping/public/openai/v0/products"
        params = {
            "countryCode": "US",
            "q": query,
            "size": size,
            "min_price": min_price,
            "max_price": max_price,
        }

        # Send the request and parse the response
        response = requests.get(base_url, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            products = data["products"]
            print(response.content)
            # Print the products
            rows = []
            for product in products:
                rows.append([product["name"], product["price"], product["url"], product["attributes"]])
            description = (
                "The response is a dataframe with the following columns: name, price, url, attributes. "
                "The attributes column is a list of tags. "
                "The price is in the format of $xx.xx."
            )
            return pd.DataFrame(rows, columns=["name", "price", "url", "attributes"]), description
        else:
            print(f"Error: {response.status_code}")


@test_plugin(name="test KlarnaSearch", description="test")
def test_call(api_call):
    question = "t shirts"
    result, description = api_call(query=question)
    print(result, description)
