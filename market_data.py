import os
from dotenv import load_dotenv
import requests
import json
import math
import time

load_dotenv()
api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

url = "https://www.alphavantage.co/query"

def extract_price(data: dict) -> float:
    quote = data.get("Global Quote")

    if quote is None:
        raise ValueError("Global Quote is missing")

    price = quote.get("05. price")

    if price is None:
        raise ValueError("Price is missing")

    try:
        price = float(price)
    except (ValueError, TypeError):
        raise ValueError("Invalid price value")

    if price <= 0 or not math.isfinite(price):
        raise ValueError("Price must be a positive finite number")

    return price

def get_current_prices(symbols: list[str]) -> tuple[dict[str, float], dict[str, str]]:
    prices = {}
    errors = {}

    for index, symbol in enumerate(symbols):
        if index > 0:
            time.sleep(1.2)
            
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": api_key
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()

            if "Note" in data or "Information" in data:
                errors[symbol] = data.get("Note") or data.get("Information")
                break

            price = extract_price(data)
            prices[symbol] = price

        except requests.exceptions.RequestException as error:
            errors[symbol] = str(error)    
            
        except ValueError as error:
            errors[symbol] = str(error)

    return prices, errors

# if __name__ == "__main__":
    
#     with open("sample_quote.json", "w", encoding="utf-8") as file:
#         json.dump(data, file, indent=4)