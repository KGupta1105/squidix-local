import os
import requests
from dotenv import load_dotenv
from config.settings import get_squidex_token, get_headers

load_dotenv()

SQUIDEX_URL = os.getenv("SQUIDEX_URL")
APP_NAME = os.getenv("SQUIDEX_APP_NAME")

def get_schemas(headers):
    url = f"{SQUIDEX_URL}/api/apps/{APP_NAME}/schemas"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("items", [])

def delete_schema(name, headers):
    url = f"{SQUIDEX_URL}/api/apps/{APP_NAME}/schemas/{name}"
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        print(f"🗑️ Deleted schema: {name}")
    else:
        print(f"⚠️ Failed to delete {name} - {response.status_code}: {response.text}")

def main():
    token = get_squidex_token()
    headers = get_headers(token)
    schemas = get_schemas(headers)

    migrated_schemas = [s for s in schemas if s.get("type") == "Component" or s.get("category") == "Templates"]
    print(f"Found {len(migrated_schemas)} schemas in 'Component' and 'Template' type.")

    for schema in migrated_schemas:
        delete_schema(schema["name"], headers)

if __name__ == "__main__":
    main()
