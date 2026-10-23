import requests
import sys

url = "http://127.0.0.1:8000/prediction/location"
payload = {
    "latitude": 27.041,
    "longitude": 88.2663
}

try:
    response = requests.post(url, json=payload)
    response.raise_for_status()
    print("API Response:", response.json())
except Exception as e:
    print("Error:", e)
    if hasattr(e, 'response') and e.response is not None:
        print(e.response.text)
