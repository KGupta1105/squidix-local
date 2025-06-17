#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

class S3AssetDeleter:
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
    
    def list_s3_objects(self, prefix="assets/"):
        """
        List all objects in S3 bucket with given prefix
        """
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
            
            objects = []
            for page in pages:
                if 'Contents' in page:
                    objects.extend(page['Contents'])
            
            print("Found {} objects in S3 with prefix '{}'".format(len(objects), prefix))
            return objects
            
        except Exception as e:
            print("Error listing S3 objects: {}".format(str(e)))
            return []
    
    def batch_delete_objects(self, s3_keys):
        """
        Delete multiple objects from S3 using batch delete
        """
        if not s3_keys:
            print("No objects to delete")
            return {'deleted': [], 'failed': []}
        
        # S3 batch delete can handle up to 1000 objects at once
        batch_size = 1000
        deleted_objects = []
        failed_objects = []
        
        for i in range(0, len(s3_keys), batch_size):
            batch = s3_keys[i:i + batch_size]
            
            # Prepare delete request
            delete_request = {
                'Objects': [{'Key': key} for key in batch]
            }
            
            try:
                response = self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete=delete_request
                )
                
                # Track successful deletions
                if 'Deleted' in response:
                    deleted_objects.extend([obj['Key'] for obj in response['Deleted']])
                
                # Track failed deletions
                if 'Errors' in response:
                    for error in response['Errors']:
                        failed_objects.append({
                            'key': error['Key'],
                            'error': error['Message']
                        })
                        print("Failed to delete {}: {}".format(error['Key'], error['Message']))
                
                print("Batch delete completed: {} deleted, {} failed".format(
                    len(response.get('Deleted', [])), 
                    len(response.get('Errors', []))
                ))
                
            except Exception as e:
                print("Batch delete failed: {}".format(str(e)))
                failed_objects.extend([{'key': key, 'error': str(e)} for key in batch])
        
        print("Total deletion results: {} deleted, {} failed".format(len(deleted_objects), len(failed_objects)))
        return {
            'deleted': deleted_objects,
            'failed': failed_objects
        }
    
    def delete_all_assets_by_prefix(self, prefix="assets/"):
        """
        Delete all assets from S3 bucket with assets/ prefix
        """
        print("Starting deletion of all objects with prefix '{}'".format(prefix))
        
        # List all objects with assets/ prefix
        objects = self.list_s3_objects(prefix)
        
        if not objects:
            print("No objects found to delete")
            return True
        
        # Extract keys
        s3_keys = [obj['Key'] for obj in objects]
        
        print("Preparing to delete {} objects...".format(len(s3_keys)))
        
        # Perform batch delete
        result = self.batch_delete_objects(s3_keys)
        
        success_count = len(result['deleted'])
        failure_count = len(result['failed'])
        
        print("Deletion completed: {}/{} objects deleted".format(success_count, len(s3_keys)))
        
        if failure_count > 0:
            print("{} objects failed to delete".format(failure_count))
        
        return failure_count == 0

def main():
    """
    Delete migrated assets from S3 bucket
    """
    print("Starting S3 asset deletion")
    
    # Initialize deleter
    deleter = S3AssetDeleter()
    
    try:
        # Check S3 bucket accessibility
        if not deleter.check_bucket_exists():
            print("Cannot access S3 bucket. Please check your AWS credentials and bucket configuration.")
            return
        
        # Delete all assets with prefix
        print("Deleting ALL assets with prefix 'assets/'")
        success = deleter.delete_all_assets_by_prefix("assets/")
        
        if success:
            print("Asset deletion completed successfully!")
        else:
            print("Asset deletion completed with errors.")
            
    except Exception as e:
        print("Deletion failed with error: {}".format(str(e)))
        raise

if __name__ == "__main__":
    main()
