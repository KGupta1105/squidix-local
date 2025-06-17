#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from services.contentful_content import ContentfulContentService
from services.mongodb import MongoDBService
from core.content_transformer import ContentTransformer

load_dotenv()

def migrate():
    """
    Migrate content from Contentful to MongoDB
    """
    print("Starting Contentful to MongoDB content migration")
    
    # Initialize services
    contentful_service = ContentfulContentService()
    mongodb_service = MongoDBService()
    transformer = ContentTransformer()
    
    try:
        # Test MongoDB connection
        print("Testing MongoDB connection...")
        if not mongodb_service.test_connection():
            print("Cannot connect to MongoDB. Please check your connection string and credentials.")
            return
        
        # Load asset mapping if available (from S3 migration)
        print("Loading asset mapping...")
        asset_mapping = transformer.load_asset_mapping()
        
        # Fetch all content from Contentful grouped by content type
        print("Fetching content from Contentful...")
        content_data = contentful_service.get_all_content_with_types(limit=100)
        
        if not content_data:
            print("No content found to migrate")
            return
        
        print("Found {} content types to migrate".format(len(content_data)))
        
        # Transform content for MongoDB
        print("Transforming content for MongoDB...")
        transformed_data = transformer.transform_content_by_type(content_data, asset_mapping)
        
        # Migration strategy: Create separate collection for each content type
        successful_migrations = 0
        failed_migrations = 0
        total_entries_migrated = 0
        
        for content_type, type_data in transformed_data.items():
            print("Migrating content type: {}".format(content_type))
            
            entries = type_data.get("entries", [])
            if not entries:
                print("No entries found for content type: {}".format(content_type))
                continue
            
            # Create collection name (use content type as collection name)
            collection_name = content_type
            
            try:
                # Insert all entries for this content type
                inserted_ids = mongodb_service.insert_documents(collection_name, entries)
                
                if inserted_ids:
                    successful_migrations += 1
                    total_entries_migrated += len(inserted_ids)
                    print("Successfully migrated {} entries for content type {}".format(
                        len(inserted_ids), content_type))
                    
                    # Create indexes for better performance
                    mongodb_service.create_index(collection_name, "migration_metadata.contentful_id")
                    mongodb_service.create_index(collection_name, "sys.content_type")
                    mongodb_service.create_index(collection_name, "sys.created_at")
                    
                else:
                    failed_migrations += 1
                    print("Failed to migrate content type: {}".format(content_type))
                    
            except Exception as e:
                failed_migrations += 1
                print("Error migrating content type {}: {}".format(content_type, str(e)))
        
        # Create migration summary
        summary = transformer.create_migration_summary(transformed_data)
        
        # Store migration summary in a special collection
        summary_doc = {
            **summary["migration_summary"],
            "successful_migrations": successful_migrations,
            "failed_migrations": failed_migrations,
            "total_entries_migrated": total_entries_migrated
        }
        
        mongodb_service.insert_document("migration_summary", summary_doc)
        
        # Show final results
        print("Content migration completed!")
        print("Results: {}/{} content types successfully migrated".format(
            successful_migrations, len(transformed_data)))
        print("Total entries migrated: {}".format(total_entries_migrated))
        
        if failed_migrations > 0:
            print("{} content types failed to migrate".format(failed_migrations))
        
        print("Migration complete.")
        
        # List all collections created
        collections = mongodb_service.list_collections()
        print("Collections created in MongoDB: {}".format(collections))
            
    except Exception as e:
        print("Migration failed with error: {}".format(str(e)))
        raise
    finally:
        # Close MongoDB connection
        mongodb_service.close_connection()

if __name__ == "__main__":
    migrate()
