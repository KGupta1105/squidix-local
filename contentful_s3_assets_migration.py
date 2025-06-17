#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from services.contentful_assets import ContentfulAssetsService
from services.aws_s3 import S3AssetService
from core.asset_transformer import AssetTransformer

load_dotenv()

def migrate():
    """
    Migrate assets from Contentful to AWS S3
    """
    print("Starting Contentful to S3 asset migration")
    
    # Initialize services
    contentful_service = ContentfulAssetsService()
    s3_service = S3AssetService()
    transformer = AssetTransformer()
    
    try:
        # Check S3 bucket accessibility first
        print("Checking S3 bucket accessibility...")
        if not s3_service.check_bucket_exists():
            print("Cannot access S3 bucket. Please check your AWS credentials and bucket configuration.")
            return
        
        # Fetch assets from Contentful (limit to 100)
        print("Fetching assets from Contentful...")
        raw_assets, total = contentful_service.get_assets_batch(limit=100, skip=0)
        assets = []
        for asset in raw_assets:
            file_info = contentful_service.extract_file_info(asset)
            if file_info:
                assets.append(file_info)
        
        print("Found {} valid assets out of {} total (limited to 100)".format(len(assets), total))
        
        if not assets:
            print("No assets found to migrate")
            return
        
        print("Found {} assets to process".format(len(assets)))
        
        # Process asset information
        print("Processing assets...")
        asset_data = []
        successful_uploads = 0
        failed_uploads = 0
        
        for asset_info in assets:
            print("Processing asset: {} (ID: {})".format(
                asset_info.get('filename'), asset_info.get('asset_id')))
            
            # Upload to S3
            s3_result = s3_service.upload_asset_to_s3(asset_info)
            
            if s3_result:
                successful_uploads += 1
                transformed = transformer.transform_asset_for_output(asset_info, s3_result)
                print("Successfully migrated: {}".format(asset_info.get('filename')))
            else:
                failed_uploads += 1
                transformed = transformer.transform_asset_for_output(asset_info)
                print("Failed to migrate: {}".format(asset_info.get('filename')))
            
            asset_data.append(transformed)
        
        # Show final results
        total_assets = len(assets)
        print("Asset migration completed!")
        print("Results: {}/{} assets successfully migrated".format(successful_uploads, total_assets))
        if failed_uploads > 0:
            print("{} assets failed to migrate".format(failed_uploads))
        
        print("Migration complete.")
            
    except Exception as e:
        print("Migration failed with error: {}".format(str(e)))
        raise

if __name__ == "__main__":
    migrate()
