import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_squidex_token():
    url = f"{os.getenv('SQUIDEX_URL')}/identity-server/connect/token"
    payload = {
        "client_id": os.getenv("SQUIDEX_CLIENT_ID"),
        "client_secret": os.getenv("SQUIDEX_CLIENT_SECRET"),
        "grant_type": "client_credentials",
        "scope": "squidex-api"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(url, data=payload, headers=headers)
    response.raise_for_status()
    return response.json().get("access_token")

def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
