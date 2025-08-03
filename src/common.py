import httpx
from src.context import get_api_key

API_BASE_URL = "https://www.alphavantage.co/query"


def _make_api_request(function_name: str, params: dict, datatype: str = "json") -> dict | str:
    """Helper function to make API requests and handle responses."""
    params.update({
        "function": function_name,
        "apikey": get_api_key()
    })
    
    with httpx.Client() as client:
        response = client.get(API_BASE_URL, params=params)
        response.raise_for_status()
        return response.text if datatype == "csv" else response.json()