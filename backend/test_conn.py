import requests
import json

url = "http://127.0.0.1:8001/v1/models"
try:
    response = requests.get(url, timeout=5)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:100]}")
except Exception as e:
    print(f"Error connecting to 127.0.0.1:8001: {e}")

url = "http://localhost:8001/v1/models"
try:
    response = requests.get(url, timeout=5)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:100]}")
except Exception as e:
    print(f"Error connecting to localhost:8001: {e}")
