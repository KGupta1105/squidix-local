import requests
import os
from dotenv import load_dotenv

load_dotenv()

CF_SPACE_ID = os.getenv("CONTENTFUL_SPACE_ID")
CF_ENVIRONMENT_ID = os.getenv("CONTENTFUL_ENVIRONMENT_ID", "staging-2025-05-27")
CF_CMA_TOKEN = os.getenv("CONTENTFUL_CMA_TOKEN")

def get_all_content_types():
    url = f"https://api.contentful.com/spaces/{CF_SPACE_ID}/environments/{CF_ENVIRONMENT_ID}/content_types"
    headers = {
        "Authorization": f"Bearer {CF_CMA_TOKEN}",
        "Content-Type": "application/vnd.contentful.management.v1+json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json().get("items", [])