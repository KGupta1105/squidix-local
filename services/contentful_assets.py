import logging
from services.contentful_base import ContentfulClient

logger = logging.getLogger(__name__)

class ContentfulAssetsService:
    def __init__(self):
        self.client = ContentfulClient()
    
    def get_all_assets(self, limit=1000):
        """
        Get all assets from Contentful
        """
        return self.client.get_all_paginated_data("assets", limit=limit)
    
    def get_assets_batch(self, limit=1000, skip=0):
        """
        Get a batch of assets from Contentful
        """
        return self.client.get_paginated_data("assets", limit=limit, skip=skip)
    
    def extract_file_info(self, asset):
        """
        Extract file information from Contentful asset
        """
        try:
            fields = asset.get("fields", {})
            file_info = fields.get("file", {})
            
            # Handle localized content (usually 'en-US' is the default locale)
            if isinstance(file_info, dict) and "en-US" in file_info:
                file_info = file_info["en-US"]
            elif isinstance(file_info, dict) and len(file_info) > 0:
                # Take the first available locale
                file_info = list(file_info.values())[0]
            
            if not file_info:
                return None
                
            # Extract title and description with locale handling
            title = fields.get("title", {})
            if isinstance(title, dict):
                title = title.get("en-US", "Untitled")
            else:
                title = title or "Untitled"
            
            description = fields.get("description", {})
            if isinstance(description, dict):
                description = description.get("en-US", "")
            else:
                description = description or ""
            
            return {
                "asset_id": asset.get("sys", {}).get("id"),
                "title": title,
                "description": description,
                "filename": file_info.get("fileName", "unknown"),
                "url": file_info.get("url", "").replace("//", "https://") if file_info.get("url") else "",
                "content_type": file_info.get("contentType", ""),
                "size": file_info.get("details", {}).get("size", 0),
                "width": file_info.get("details", {}).get("image", {}).get("width"),
                "height": file_info.get("details", {}).get("image", {}).get("height"),
                "created_at": asset.get("sys", {}).get("createdAt"),
                "updated_at": asset.get("sys", {}).get("updatedAt")
            }
        except Exception as e:
            logger.error(f"Error extracting file info from asset {asset.get('sys', {}).get('id', 'unknown')}: {str(e)}")
            return None
    
    def get_processed_assets(self):
        """
        Get all assets with processed file information
        """
        assets = self.get_all_assets()
        processed_assets = []
        
        for asset in assets:
            file_info = self.extract_file_info(asset)
            if file_info:
                processed_assets.append(file_info)
        
        logger.info(f"Processed {len(processed_assets)} valid assets out of {len(assets)} total assets")
        return processed_assets
