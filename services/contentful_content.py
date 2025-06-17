import logging
from services.contentful_base import ContentfulClient

logger = logging.getLogger(__name__)

class ContentfulContentService:
    def __init__(self):
        self.client = ContentfulClient()
    
    def get_all_entries(self, content_type=None, limit=1000):
        """
        Get all entries from Contentful, optionally filtered by content type
        """
        if content_type:
            # Use the direct API call with content_type parameter
            return self._get_entries_by_content_type(content_type, limit)
        else:
            return self.client.get_all_paginated_data("entries")
    
    def _get_entries_by_content_type(self, content_type, limit=1000):
        """
        Get all entries for a specific content type using direct API calls
        """
        all_items = []
        skip = 0
        
        while True:
            params = {
                "content_type": content_type,
                "limit": min(limit, 1000),  # Contentful max limit is 1000
                "skip": skip
            }
            
            try:
                data = self.client.make_request("entries", params)
                items = data.get("items", [])
                total = data.get("total", 0)
                
                all_items.extend(items)
                
                if skip + len(items) >= total or len(items) == 0:
                    break
                    
                skip += len(items)
                
            except Exception as e:
                print("Error fetching entries for content type {}: {}".format(content_type, str(e)))
                break
        
        return all_items
    
    def get_entries_batch(self, content_type=None, limit=100, skip=0):
        """
        Get a batch of entries from Contentful
        """
        params = {"limit": limit, "skip": skip}
        if content_type:
            params["content_type"] = content_type
        
        return self.client.get_paginated_data("entries", **params)
    
    def get_entry_by_id(self, entry_id):
        """
        Get a specific entry by ID
        """
        return self.client.get_data("entries/{}".format(entry_id))
    
    def extract_entry_info(self, entry):
        """
        Extract and normalize entry information from Contentful
        """
        try:
            sys_info = entry.get("sys", {})
            fields = entry.get("fields", {})
            
            # Extract system information
            entry_info = {
                "contentful_id": sys_info.get("id"),
                "content_type": sys_info.get("contentType", {}).get("sys", {}).get("id"),
                "created_at": sys_info.get("createdAt"),
                "updated_at": sys_info.get("updatedAt"),
                "version": sys_info.get("version"),
                "space_id": sys_info.get("space", {}).get("sys", {}).get("id"),
                "environment_id": sys_info.get("environment", {}).get("sys", {}).get("id"),
            }
            
            # Process fields with locale handling
            processed_fields = {}
            for field_name, field_value in fields.items():
                processed_fields[field_name] = self._process_field_value(field_value)
            
            entry_info["fields"] = processed_fields
            
            return entry_info
            
        except Exception as e:
            print("Error extracting entry info from entry {}: {}".format(
                entry.get("sys", {}).get("id", "unknown"), str(e)))
            return None
    
    def _process_field_value(self, field_value):
        """
        Process field values, handling localization and references
        """
        # If it's a localized field (has locale keys like 'en-US')
        if isinstance(field_value, dict):
            # Check if it looks like localized content
            if any(key in field_value for key in ['en-US', 'en', 'en-GB']):
                # Return the first available locale, preferring en-US
                for locale in ['en-US', 'en', 'en-GB']:
                    if locale in field_value:
                        return self._process_field_value(field_value[locale])
                # If no preferred locale, return the first available
                if field_value:
                    return self._process_field_value(list(field_value.values())[0])
                return None
            
            # Check if it's a reference to another entry or asset
            elif field_value.get("sys", {}).get("type") in ["Link", "Entry", "Asset"]:
                return self._process_reference(field_value)
            
            # Regular object, return as-is
            else:
                return field_value
        
        # If it's a list, process each item
        elif isinstance(field_value, list):
            return [self._process_field_value(item) for item in field_value]
        
        # Primitive value, return as-is
        else:
            return field_value
    
    def _process_reference(self, reference):
        """
        Process Contentful references (links to other entries or assets)
        """
        try:
            sys_info = reference.get("sys", {})
            link_type = sys_info.get("linkType", sys_info.get("type"))
            
            processed_ref = {
                "contentful_id": sys_info.get("id"),
                "link_type": link_type,
                "type": "reference"
            }
            
            # If it's an asset reference, we might want to include the S3 URL later
            if link_type == "Asset":
                processed_ref["asset_type"] = "asset"
            elif link_type == "Entry":
                processed_ref["entry_type"] = "entry"
            
            return processed_ref
            
        except Exception as e:
            print("Error processing reference: {}".format(str(e)))
            return reference
    
    def get_entries_by_content_type(self, content_type, limit=1000):
        """
        Get all entries of a specific content type
        """
        try:
            print("Fetching entries for content type: {}".format(content_type))
            entries = self.get_all_entries(content_type=content_type, limit=limit)
            
            processed_entries = []
            for entry in entries:
                processed_entry = self.extract_entry_info(entry)
                if processed_entry:
                    processed_entries.append(processed_entry)
            
            print("Processed {} entries for content type {}".format(len(processed_entries), content_type))
            return processed_entries
            
        except Exception as e:
            print("Error getting entries for content type {}: {}".format(content_type, str(e)))
            return []
    
    def get_all_content_with_types(self, limit=1000):
        """
        Get all content grouped by content type
        """
        try:
            # First get all content types
            from services.contentful_schemas import ContentfulSchemasService
            schemas_service = ContentfulSchemasService()
            content_types = schemas_service.get_all_content_types()
            
            all_content = {}
            
            for content_type in content_types:
                content_type_id = content_type.get("sys", {}).get("id")
                if content_type_id:
                    entries = self.get_entries_by_content_type(content_type_id, limit)
                    all_content[content_type_id] = {
                        "content_type_info": content_type,
                        "entries": entries,
                        "count": len(entries)
                    }
            
            return all_content
            
        except Exception as e:
            print("Error getting all content with types: {}".format(str(e)))
            return {}
