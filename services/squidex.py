import requests
import os
import json
from dotenv import load_dotenv
from config.settings import get_squidex_token, get_headers

load_dotenv()

SQUIDEX_URL = os.getenv("SQUIDEX_URL", "http://localhost:8080")
APP_NAME = os.getenv("SQUIDEX_APP_NAME")


def get_schema_id_map():
    url = f"{SQUIDEX_URL}/api/apps/{APP_NAME}/schemas"
    token = get_squidex_token()
    headers = get_headers(token)
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return {
        schema["name"]: schema["id"]
        for schema in response.json().get("items", [])
    }

def push_schema_to_squidex(schema_json):
    name = schema_json.get("name")
    url = f"{SQUIDEX_URL}/api/apps/{APP_NAME}/schemas/{name}"
    token = get_squidex_token()
    headers = get_headers(token)

    # Check if schema already exists
    get_resp = requests.get(url, headers=headers)

    if get_resp.status_code == 200:
        print(f"🔄 Schema exists: {name} → Updating...")

        # Get the current schema to preserve existing structure
        current_schema = get_resp.json()
        
        # Update the schema with new structure but preserve properties at top level
        updated_schema = schema_json.copy()
        
        # Move schema-level properties from nested structure to top level for Squidex API
        if "properties" in updated_schema:
            label = updated_schema["properties"].get("label", name)
            hints = updated_schema["properties"].get("description", "")
            # Remove only the schema-level properties and add them at top level
            del updated_schema["properties"]
            updated_schema["label"] = label
            updated_schema["hints"] = hints

        
        put_resp = requests.put(url, headers=headers, data=json.dumps(updated_schema))
        if put_resp.status_code >= 400:
            print(f"❌ Failed to update schema: {name} ({put_resp.status_code})")
            print(put_resp.text)
        else:
            schema_id = get_resp.json().get("id")
            print(f"✅ Successfully updated schema: {name} with label: {label}")
            print(f"   📋 Schema ID: {schema_id}")
            
            # Update individual Component fields with schemaIds
            for field in updated_schema.get("fields", []):
                if field.get("properties", {}).get("fieldType") == "Component":
                    field_name = field.get("name")
                    schema_ids = field.get("properties", {}).get("schemaIds", [])
                    
                    if schema_ids:
                        # Find the field ID from current schema
                        current_field = None
                        for curr_field in current_schema.get("fields", []):
                            if curr_field.get("name") == field_name:
                                current_field = curr_field
                                break
                        
                        if current_field and current_field.get("fieldId"):
                            field_id = current_field["fieldId"]
                            field_update_url = f"{SQUIDEX_URL}/api/apps/{APP_NAME}/schemas/{name}/fields/{field_id}"
                            field_payload = {
                                "properties": {
                                    "fieldType": "Component",
                                    "schemaIds": schema_ids,
                                    "label": field.get("properties", {}).get("label", field_name),
                                    "isRequired": field.get("properties", {}).get("isRequired", False),
                                    "isRequiredOnPublish": field.get("properties", {}).get("isRequiredOnPublish", False),
                                    "isHalfWidth": field.get("properties", {}).get("isHalfWidth", False)
                                }
                            }
                            
                            field_resp = requests.put(field_update_url, headers=headers, data=json.dumps(field_payload))
                            
                            if field_resp.status_code == 200:
                                print(f"   ✅ Updated field {field_name} with {len(schema_ids)} references")
                            else:
                                print(f"   ❌ Field {field_name} update failed: {field_resp.status_code}")
            
            # Publish the schema to make changes take effect
            publish_url = f"{SQUIDEX_URL}/api/apps/{APP_NAME}/schemas/{name}/publish"
            publish_resp = requests.put(publish_url, headers=headers)
            if publish_resp.status_code == 200:
                print(f"   ✅ Schema published successfully")
            else:
                print(f"   ⚠️ Schema publish failed: {publish_resp.status_code}")
            
            # Verify the schema was updated with correct field properties
            verify_resp = requests.get(url, headers=headers)
            if verify_resp.status_code == 200:
                updated_schema_data = verify_resp.json()
                for field in updated_schema_data.get("fields", []):
                    if field.get("properties", {}).get("fieldType") == "Component":
                        field_name = field.get("name")
                        schema_ids = field.get("properties", {}).get("schemaIds", [])
                        if schema_ids:
                            print(f"   ✅ Field {field_name} has {len(schema_ids)} schema IDs")
                        else:
                            print(f"   ⚠️ Field {field_name} has empty schemaIds")

    else:
        print(f"➕ Creating new schema: {name}")
        
        # Prepare schema for creation with properties at top level
        create_schema = schema_json.copy()
        if "properties" in create_schema:
            label = create_schema["properties"].get("label", name)
            hints = create_schema["properties"].get("description", "")
            # Remove only the schema-level properties and add them at top level
            del create_schema["properties"]
            create_schema["label"] = label
            create_schema["hints"] = hints
        
        post_url = f"{SQUIDEX_URL}/api/apps/{APP_NAME}/schemas"
        post_resp = requests.post(post_url, headers=headers, data=json.dumps(create_schema))
        if post_resp.status_code >= 400:
            print(f"❌ Failed to create schema: {name} ({post_resp.status_code})")
            print(post_resp.text)
        else:
            created_schema = post_resp.json()
            schema_id = created_schema.get("id")
            print(f"✅ Successfully created schema: {name} with label: {label}")
            print(f"   📋 Schema ID: {schema_id}")
