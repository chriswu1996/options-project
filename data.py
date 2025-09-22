import pandas as pd
import requests

DERIBIT_API_BASE = "https://www.deribit.com/api/v2"

def get_price(ticker, currency="usd"):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": currency,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data[ticker][currency]
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def get_options_data(ticker, exp):
    # TODO: Calculate synthetic futures price ourselves
    ticker = ticker.upper()
    res = requests.get(f"{DERIBIT_API_BASE}/public/get_book_summary_by_currency", params={'currency': ticker, 'kind': 'option'}, timeout=10).json()['result']
    res = pd.DataFrame([x for x in res if exp.strftime('%d%b%y').upper() in x['instrument_name']])[['instrument_name', 'mark_iv', 'underlying_price']]  # mark_price, timestamp
    return res