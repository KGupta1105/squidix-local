import json
from datetime import datetime

class ContentTransformer:
    def __init__(self):
        pass
    
    def transform_content_for_mongodb(self, entry_info, asset_mapping=None):
        """
        Transform Contentful entry for MongoDB storage
        """
        try:
            transformed = {
                # MongoDB metadata
                "_id": entry_info.get("contentful_id"),  # Use Contentful ID as MongoDB _id
                "migration_metadata": {
                    "source": "contentful",
                    "migrated_at": datetime.now().isoformat(),
                    "content_type": entry_info.get("content_type"),
                    "contentful_id": entry_info.get("contentful_id"),
                    "version": entry_info.get("version"),
                    "space_id": entry_info.get("space_id"),
                    "environment_id": entry_info.get("environment_id")
                },
                
                # Contentful system info
                "sys": {
                    "created_at": entry_info.get("created_at"),
                    "updated_at": entry_info.get("updated_at"),
                    "content_type": entry_info.get("content_type")
                },
                
                # Content fields
                "fields": self._process_fields_for_mongodb(entry_info.get("fields", {}), asset_mapping)
            }
            
            return transformed
            
        except Exception as e:
            print("Error transforming content for MongoDB: {}".format(str(e)))
            return None
    
    def _process_fields_for_mongodb(self, fields, asset_mapping=None):
        """
        Process content fields, replacing asset references with S3 URLs
        """
        processed_fields = {}
        
        for field_name, field_value in fields.items():
            processed_fields[field_name] = self._process_field_value_for_mongodb(field_value, asset_mapping)
        
        return processed_fields
    
    def _process_field_value_for_mongodb(self, field_value, asset_mapping=None):
        """
        Process individual field values for MongoDB
        """
        if isinstance(field_value, dict):
            # Check if it's an asset reference
            if field_value.get("type") == "reference" and field_value.get("link_type") == "Asset":
                return self._resolve_asset_reference(field_value, asset_mapping)
            
            # Check if it's an entry reference
            elif field_value.get("type") == "reference" and field_value.get("link_type") == "Entry":
                return self._resolve_entry_reference(field_value)
            
            # Regular object, process recursively
            else:
                processed_obj = {}
                for key, value in field_value.items():
                    processed_obj[key] = self._process_field_value_for_mongodb(value, asset_mapping)
                return processed_obj
        
        elif isinstance(field_value, list):
            return [self._process_field_value_for_mongodb(item, asset_mapping) for item in field_value]
        
        else:
            return field_value
    
    def _resolve_asset_reference(self, asset_ref, asset_mapping=None):
        """
        Resolve asset reference to S3 URL if available
        """
        contentful_asset_id = asset_ref.get("contentful_id")
        
        # If we have asset mapping (from S3 migration), use S3 URL
        if asset_mapping and contentful_asset_id in asset_mapping:
            asset_info = asset_mapping[contentful_asset_id]
            return {
                "type": "asset",
                "contentful_id": contentful_asset_id,
                "s3_url": asset_info.get("s3_url"),
                "s3_key": asset_info.get("s3_key"),
                "original_url": asset_info.get("original_url")
            }
        
        # Otherwise, keep the reference as-is
        return {
            "type": "asset_reference",
            "contentful_id": contentful_asset_id,
            "note": "Asset not migrated to S3 yet"
        }
    
    def _resolve_entry_reference(self, entry_ref):
        """
        Resolve entry reference
        """
        return {
            "type": "entry_reference",
            "contentful_id": entry_ref.get("contentful_id"),
            "link_type": "Entry"
        }
    
    def transform_content_by_type(self, content_data, asset_mapping=None):
        """
        Transform content grouped by content type
        """
        transformed_by_type = {}
        
        for content_type, type_data in content_data.items():
            print("Transforming content type: {}".format(content_type))
            
            transformed_entries = []
            entries = type_data.get("entries", [])
            
            for entry in entries:
                transformed_entry = self.transform_content_for_mongodb(entry, asset_mapping)
                if transformed_entry:
                    transformed_entries.append(transformed_entry)
            
            transformed_by_type[content_type] = {
                "content_type_info": type_data.get("content_type_info"),
                "entries": transformed_entries,
                "count": len(transformed_entries)
            }
            
            print("Transformed {} entries for content type {}".format(len(transformed_entries), content_type))
        
        return transformed_by_type
    
    def load_asset_mapping(self, mapping_file="output/assets/asset_mapping.json"):
        """
        Load asset mapping from S3 migration
        """
        try:
            with open(mapping_file, 'r') as f:
                asset_mapping = json.load(f)
                print("Loaded asset mapping with {} assets".format(len(asset_mapping)))
                return asset_mapping
        except FileNotFoundError:
            print("Asset mapping file not found: {}".format(mapping_file))
            print("Assets will not be linked to S3 URLs")
            return None
        except Exception as e:
            print("Error loading asset mapping: {}".format(str(e)))
            return None
    
    def create_migration_summary(self, transformed_data):
        """
        Create a summary of the content transformation
        """
        total_entries = 0
        content_types_count = 0
        
        for content_type, type_data in transformed_data.items():
            content_types_count += 1
            total_entries += type_data.get("count", 0)
        
        summary = {
            "migration_summary": {
                "total_content_types": content_types_count,
                "total_entries": total_entries,
                "transformed_at": datetime.now().isoformat(),
                "content_types": list(transformed_data.keys())
            }
        }
        
        return summary
