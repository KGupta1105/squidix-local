#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from services.mongodb import MongoDBService

load_dotenv()

def main():
    """
    Delete all migrated content from MongoDB
    """
    print("Starting MongoDB content deletion")
    
    # Initialize MongoDB service
    mongodb_service = MongoDBService()
    
    try:
        # Test MongoDB connection
        if not mongodb_service.test_connection():
            print("Cannot connect to MongoDB. Please check your connection string and credentials.")
            return
        
        # List all collections
        collections = mongodb_service.list_collections()
        
        if not collections:
            print("No collections found in database")
            return
        
        print("Found {} collections in database".format(len(collections)))
        
        # Drop each collection completely
        deleted_collections = 0
        for collection_name in collections:
            print("Dropping collection: {}".format(collection_name))
            
            try:
                success = mongodb_service.drop_collection(collection_name)
                if success:
                    deleted_collections += 1
                    print("Successfully dropped collection: {}".format(collection_name))
                else:
                    print("Failed to drop collection: {}".format(collection_name))
            except Exception as e:
                print("Error dropping collection {}: {}".format(collection_name, str(e)))
        
        print("Content deletion completed!")
        print("Dropped {}/{} collections".format(deleted_collections, len(collections)))
        
    except Exception as e:
        print("Deletion failed with error: {}".format(str(e)))
        raise
    finally:
        # Close MongoDB connection
        mongodb_service.close_connection()

if __name__ == "__main__":
    main()
