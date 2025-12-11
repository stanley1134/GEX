import requests
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
try:
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
except:
    pass

API_KEY = os.getenv("TRADIER_API_KEY")
if not API_KEY:
    print("WARNING: Key not found in env, using default fallback")
    API_KEY = "Clty9DpKMudoRXfh9vYKee9A09r0"

def test_fetch():
    print("--- DIAGNOSTIC START ---")
    ticker = 'SPX'
    base_url = "https://api.tradier.com/v1"
    headers = {'Authorization': f'Bearer {API_KEY}', 'Accept': 'application/json'}
    
    print(f"API Key: {API_KEY[:4]}...{API_KEY[-4:]}")
    
    # 1. Price
    print("\n1. Fetching Price...")
    try:
        r = requests.get(f"{base_url}/markets/quotes", params={'symbols': ticker}, headers=headers)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print(f"Response: {r.text[:200]}")
            price = r.json()['quotes']['quote']['last']
            print(f"Price: {price}")
        else:
            print("FAILED to get price")
            return
    except Exception as e:
        print(f"ERROR: {e}")
        return

    # 2. Expirations
    print("\n2. Fetching Expirations...")
    try:
        r = requests.get(f"{base_url}/markets/options/expirations", params={'symbol': ticker}, headers=headers)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            dates = data['expirations']['date']
            print(f"Found {len(dates)} Expirations. Next 3: {dates[:3]}")
            
            today = datetime.now().date().strftime('%Y-%m-%d')
            expiry = today if today in dates else next((d for d in dates if d >= today), None)
            print(f"Target Expiry: {expiry}")
        else:
            print("FAILED to get expirations")
            return
    except Exception as e:
        print(f"ERROR: {e}")
        return

    if not expiry:
        print("No valid expiry found, stopping.")
        return

    # 3. Chain
    print(f"\n3. Fetching Chain for {expiry}...")
    try:
        r = requests.get(f"{base_url}/markets/options/chains", 
                        params={'symbol': ticker, 'expiration': expiry, 'greeks': 'true'}, 
                        headers=headers)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            options = data.get('options', {}).get('option', [])
            print(f"Found {len(options)} options")
            
            if len(options) > 0:
                print(f"Sample Option: {options[0]}")
        else:
            print("FAILED to get chain")
    except Exception as e:
        print(f"ERROR: {e}")

    print("\n--- DIAGNOSTIC END ---")

if __name__ == "__main__":
    test_fetch()
