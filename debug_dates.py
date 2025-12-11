
import sys
import os
from datetime import datetime

# Add the current directory to sys.path so we can import from webapp
sys.path.append(os.path.join(os.getcwd()))

# Import the specific function to test
from webapp.app import get_gex_data_json

print("--- STARTING DEBUG SCRIPT ---")
today = datetime.now().date().strftime('%Y-%m-%d')
print(f"Today is: {today}")

print("Attempting to fetch data for TODAY...")
result = get_gex_data_json(target_date=today)

if result:
    print(f"Success! Fetched data for: {result['expiry']}")
else:
    print("Failed to fetch data.")
