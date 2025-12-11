import requests
import os
from datetime import datetime

API_KEY = "Clty9DpKMudoRXfh9vYKee9A09r0"

def check_dates():
    ticker = 'SPX'
    base_url = "https://api.tradier.com/v1"
    headers = {'Authorization': f'Bearer {API_KEY}', 'Accept': 'application/json'}
    
    print(f"Fetching expirations for {ticker}...")
    try:
        r = requests.get(f"{base_url}/markets/options/expirations", params={'symbol': ticker, 'includeAllRoots': 'true'}, headers=headers)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            dates = data['expirations']['date']
            print(f"Type of dates: {type(dates)}")
            if isinstance(dates, list):
                print(f"First 5 dates: {dates[:5]}")
                print(f"Last 5 dates: {dates[-5:]}")
                print(f"Total dates: {len(dates)}")
                
                today = datetime.now().date().strftime('%Y-%m-%d')
                print(f"Today: {today}")
                print(f"Is today in dates? {today in dates}")
            else:
                print(f"Dates is not a list: {dates}")
        else:
            print(r.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_dates()
