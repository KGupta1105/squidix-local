import boto3
import os
import requests
from urllib.parse import urlparse
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

class S3AssetService:
    def __init__(self):
        self.access_key_id = os.getenv("SQUIDEX_AWS_ACCESS_KEY_ID")
        self.secret_access_key = os.getenv("SQUIDEX_AWS_SECRET_ACCESS_KEY")
        self.bucket_name = os.getenv("SQUIDEX_S3_BUCKET_NAME")
        self.region = os.getenv("SQUIDEX_S3_REGION", "ap-southeast-2")
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region
        )
        
        print("Initialized S3 client for bucket: {} in region: {}".format(self.bucket_name, self.region))
    
    def check_bucket_exists(self):
        """
        Check if the S3 bucket exists and is accessible
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print("S3 bucket '{}' exists and is accessible".format(self.bucket_name))
            return True
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                print("S3 bucket '{}' does not exist".format(self.bucket_name))
            elif error_code == 403:
                print("Access denied to S3 bucket '{}'".format(self.bucket_name))
            else:
                print("Error accessing S3 bucket '{}': {}".format(self.bucket_name, e))
            return False
    
    def generate_s3_key(self, asset_info):
        """
        Generate S3 key for the asset using title
        """
        import re
        
        filename = asset_info.get("filename", "unknown_file")
        title = asset_info.get("title", "")
        asset_id = asset_info.get("asset_id", "unknown")
        
        # Use title if available, otherwise use asset ID
        if title and title.strip():
            # Clean the title for use in filename (remove special characters)
            clean_title = re.sub(r'[^\w\s-]', '', title.strip())
            clean_title = re.sub(r'[-\s]+', '-', clean_title)
            s3_key = "assets/{}_{}".format(clean_title, filename)
        else:
            # Fallback to asset ID if no title
            s3_key = "assets/{}_{}".format(asset_id, filename)
        
        return s3_key
    
    def download_asset(self, url):
        """
        Download asset from Contentful URL with retry logic
        """
        import time
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                print("Attempting download (attempt {}/{}): {}".format(attempt + 1, max_retries, url))
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                print("Successfully downloaded asset")
                return response.content
            except Exception as e:
                print("Download attempt {} failed: {}".format(attempt + 1, str(e)))
                if attempt < max_retries - 1:
                    print("Retrying in {} seconds...".format(retry_delay))
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print("All download attempts failed for: {}".format(url))
                    return None
    
    def upload_asset_to_s3(self, asset_info):
        """
        Upload a single asset to S3
        """
        try:
            url = asset_info.get("url")
            if not url:
                print("No URL found for asset {}".format(asset_info.get('asset_id')))
                return None
            
            # Download the asset
            print("Downloading asset: {} from {}".format(asset_info.get('filename'), url))
            asset_data = self.download_asset(url)
            
            if not asset_data:
                return None
            
            # Generate S3 key
            s3_key = self.generate_s3_key(asset_info)
            
            # Prepare metadata
            metadata = {
                'original-url': url,
                'asset-id': asset_info.get('asset_id', ''),
                'title': asset_info.get('title', '')[:1000],  # S3 metadata has size limits
                'original-filename': asset_info.get('filename', '')
            }
            
            # Upload to S3
            print("Uploading to S3: {}".format(s3_key))
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=asset_data,
                ContentType=asset_info.get('content_type', 'application/octet-stream'),
                Metadata=metadata
            )
            
            # Generate S3 URL
            s3_url = "https://{}.s3.{}.amazonaws.com/{}".format(self.bucket_name, self.region, s3_key)
            
            print("Successfully uploaded {} to S3".format(asset_info.get('filename')))
            
            return {
                "asset_id": asset_info.get("asset_id"),
                "original_url": url,
                "s3_key": s3_key,
                "s3_url": s3_url,
                "size": asset_info.get("size"),
                "content_type": asset_info.get("content_type"),
                "filename": asset_info.get("filename"),
                "title": asset_info.get("title")
            }
            
        except Exception as e:
            print("Error uploading asset {} to S3: {}".format(asset_info.get('asset_id'), str(e)))
            return None
    
    def batch_upload_assets(self, assets_list):
        """
        Upload multiple assets to S3
        """
        results = []
        total_assets = len(assets_list)
        
        print("Starting batch upload of {} assets to S3".format(total_assets))
        
        for i, asset_info in enumerate(assets_list, 1):
            print("Processing asset {}/{}: {}".format(i, total_assets, asset_info.get('filename')))
            
            result = self.upload_asset_to_s3(asset_info)
            if result:
                results.append(result)
            else:
                print("Failed to upload asset {}".format(asset_info.get('asset_id')))
        
        print("Batch upload completed. Successfully uploaded {}/{} assets".format(len(results), total_assets))
        return results
