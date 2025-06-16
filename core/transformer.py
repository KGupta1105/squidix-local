import re

def kebab_case(name: str) -> str:
    # Handle names that are already in kebab-case
    if '-' in name and name.islower():
        return name.strip()
    
    # Convert camelCase/PascalCase to kebab-case
    # First, handle the transition from lowercase to uppercase
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
    # Then handle the transition from lowercase to uppercase
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1)
    # Handle letter followed by number (e.g., "Bt50" → "bt-50")
    s3 = re.sub(r'([a-zA-Z])(\d+)', r'\1-\2', s2)
    # Replace any remaining non-alphanumeric characters with hyphens
    s4 = re.sub(r'[^a-zA-Z0-9]+', '-', s3)
    # Convert to lowercase and strip any leading/trailing hyphens
    return s4.lower().strip('-')

def camel_case(name: str) -> str:
    parts = re.sub(r'[^a-zA-Z0-9]+', ' ', name).split()
    return parts[0].lower() + ''.join(word.capitalize() for word in parts[1:]) if parts else name.lower()

def convert_field_type(contentful_type):
    mapping = {
        "Symbol": "String",
        "Text": "RichText",
        "Boolean": "Boolean",
        "Integer": "Number",
        "Number": "Number",
        "Date": "DateTime",
        "Object": "Json",
        "Location": "Geolocation",
        "RichText": "RichText",
        "Link": "References",
        "Array": "Array"
    }
    return mapping.get(contentful_type, "String")

def transform_content_type(contentful_model, schema_id_map, resolve_references=True):
    original_name = contentful_model["name"]
    # Use the actual Contentful content type ID for schema name (from sys.id)
    contentful_id = contentful_model.get("sys", {}).get("id", "")
    
    if contentful_id:
        # Convert Contentful ID to kebab-case for Squidx (which requires valid slugs)
        schema_name = kebab_case(contentful_id)
    else:
        # Fallback to converting display name
        schema_name = kebab_case(original_name)

    fields = []
    for field in contentful_model.get("fields", []):
        if field.get("omitted", False):
            continue

        field_name = camel_case(field["id"])
        field_type = convert_field_type(field["type"])
        properties = {
            "label": field.get("name", field_name),
            "fieldType": field_type,
            "isRequired": field.get("required", False)
        }

        if field["type"] == "Array" and field.get("items", {}).get("type") == "Link":
            schema_ids = []
            
            # Extract link types from validations
            validations = field.get("items", {}).get("validations", [])
            link_types = []
            
            for validation in validations:
                if "linkContentType" in validation:
                    link_types.extend(validation["linkContentType"])

            if resolve_references and link_types:
                for link_type in link_types:
                    kebab = kebab_case(link_type)
                    resolved = schema_id_map.get(kebab)
                    if resolved:
                        schema_ids.append(resolved)
                
                if schema_ids:
                    print(f"📋 {schema_name} → Field: {field_name} → References: {link_types} → Schema IDs: {schema_ids}")

            properties.update({
                "fieldType": "Component",
                "schemaIds": schema_ids,
                "isRequired": field.get("required", False),
                "isRequiredOnPublish": False,
                "isHalfWidth": False,
                "cachedValues": {}
            })

        field_obj = {
            "name": field_name,
            "isHidden": False,
            "isLocked": False,
            "isDisabled": False,
            "partitioning": "invariant",
            "properties": properties
        }
        
        # Add cachedValues for Component fields
        if properties.get("fieldType") == "Component":
            field_obj["cachedValues"] = {
                "canUpdate": True,
                "isLocalizable": False,
                "displayName": field.get("name", field_name)
            }
        
        fields.append(field_obj)

    # Define parent template schemas that should be in Templates category
    template_schemas = [
        "Kizuna VI",
        "Mazda EDM Template",
        "Mazda Newsletter Template PROD",
        "Mazda Newsletter Template Staging"
    ]
    
    # Add Templates category for parent schemas
    if original_name in template_schemas:
        # Templates use Default type with additional properties
        transformed_schema = {
            "name": schema_name,
            "previewUrls": {},
            "properties": {
                "cachedValues": {},
                "validateOnPublish": False,
                "label": original_name,
                "description": contentful_model.get("description", ""),
                "tags": []
            },
            "category": "Templates",
            "scripts": {},
            "isPublished": True,
            "fieldRules": [],
            "fieldsInLists": [],
            "fieldsInReferences": [],
            "fields": fields,
            "type": "Default"
        }
    else:
        # Regular Component schema structure
        transformed_schema = {
            "name": schema_name,
            "fields": fields,
            "type": "Component",
            "isPublished": True,
            "properties": {
                "label": original_name,
                "description": contentful_model.get("description", ""),
                "tags": []
            }
        }
    
    return transformed_schema
