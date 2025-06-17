import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AssetTransformer:
    def __init__(self):
        pass
    
    def transform_asset_for_output(self, asset_info, s3_info=None):
        """
        Transform asset information for output/logging
        """
        transformed = {
            "contentful_asset": {
                "id": asset_info.get("asset_id"),
                "title": asset_info.get("title"),
                "filename": asset_info.get("filename"),
                "content_type": asset_info.get("content_type"),
                "size": asset_info.get("size"),
                "dimensions": {
                    "width": asset_info.get("width"),
                    "height": asset_info.get("height")
                } if asset_info.get("width") and asset_info.get("height") else None,
                "created_at": asset_info.get("created_at"),
                "updated_at": asset_info.get("updated_at"),
                "original_url": asset_info.get("url")
            }
        }
        
        if s3_info:
            transformed["s3_migration"] = {
                "s3_key": s3_info.get("s3_key"),
                "s3_url": s3_info.get("s3_url"),
                "status": "success",
                "migrated_at": datetime.now().isoformat()
            }
        else:
            transformed["s3_migration"] = {
                "status": "failed",
                "error": "Upload to S3 failed"
            }
        
        return transformed
    
    def create_migration_summary(self, total_assets, successful_uploads, failed_uploads):
        """
        Create a summary of the migration process
        """
        success_rate = (successful_uploads / total_assets * 100) if total_assets > 0 else 0
        
        summary = {
            "migration_summary": {
                "total_assets": total_assets,
                "successful_uploads": successful_uploads,
                "failed_uploads": failed_uploads,
                "success_rate": f"{success_rate:.2f}%",
                "completed_at": datetime.now().isoformat()
            }
        }
        
        return summary
    
    def save_asset_mapping(self, asset_mappings, output_path="output/assets/asset_mapping.json"):
        """
        Save asset mapping to JSON file
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(asset_mappings, f, indent=2)
            logger.info(f"Asset mapping saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving asset mapping: {str(e)}")
    
    def save_migration_report(self, migration_data, output_path="output/assets/migration_report.json"):
        """
        Save detailed migration report
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(migration_data, f, indent=2)
            logger.info(f"Migration report saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving migration report: {str(e)}")
