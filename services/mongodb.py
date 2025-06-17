import os
from urllib.parse import quote_plus
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

load_dotenv()

class MongoDBService:
    def __init__(self):
        self.connection_string = os.getenv("MONGODB_CONNECTION_STRING")
        self.database_name = os.getenv("MONGODB_DATABASE_NAME", "squidex")
        
        # Initialize MongoDB client
        try:
            # Fix connection string if it has URL encoding issues
            connection_string = self._fix_connection_string(self.connection_string)
            self.client = MongoClient(
                connection_string, 
                serverSelectionTimeoutMS=30000, 
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                retryWrites=True,
                w='majority'
            )
            self.db = self.client[self.database_name]
            print("Initialized MongoDB client for database: {}".format(self.database_name))
        except Exception as e:
            print("Error initializing MongoDB client: {}".format(str(e)))
            self.client = None
            self.db = None
    
    def _fix_connection_string(self, connection_string):
        """
        Fix connection string by URL-encoding username and password if needed
        """
        if not connection_string:
            return connection_string
        
        try:
            # Check if it's a mongodb+srv connection string with credentials
            if "mongodb+srv://" in connection_string and "@" in connection_string:
                # Extract parts: mongodb+srv://username:password@cluster...
                protocol_and_rest = connection_string.split("://", 1)
                protocol = protocol_and_rest[0]
                rest = protocol_and_rest[1]
                
                # Find the last @ to separate credentials from host
                # This handles passwords that contain @ symbols
                at_positions = [i for i, char in enumerate(rest) if char == '@']
                if at_positions:
                    # Use the last @ as the separator
                    last_at = at_positions[-1]
                    credentials_part = rest[:last_at]
                    host_part = rest[last_at + 1:]
                    
                    if ":" in credentials_part:
                        # Find the first : to separate username from password
                        colon_pos = credentials_part.find(":")
                        username = credentials_part[:colon_pos]
                        password = credentials_part[colon_pos + 1:]
                        
                        # URL encode username and password
                        encoded_username = quote_plus(username)
                        encoded_password = quote_plus(password)
                        
                        # Reconstruct connection string
                        fixed_string = "{}://{}:{}@{}".format(
                            protocol, encoded_username, encoded_password, host_part)
                        print("Fixed connection string encoding")
                        return fixed_string
            
            return connection_string
            
        except Exception as e:
            print("Error fixing connection string: {}".format(str(e)))
            return connection_string
    
    def test_connection(self):
        """
        Test MongoDB connection
        """
        try:
            # The ping command is cheap and does not require auth.
            self.client.admin.command('ping')
            print("MongoDB connection successful!")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print("MongoDB connection failed: {}".format(str(e)))
            return False
        except Exception as e:
            print("Error testing MongoDB connection: {}".format(str(e)))
            return False
    
    def get_collection(self, collection_name):
        """
        Get a specific collection
        """
        if self.db is None:
            print("Database not initialized")
            return None
        return self.db[collection_name]
    
    def insert_document(self, collection_name, document):
        """
        Insert a single document into a collection
        """
        try:
            collection = self.get_collection(collection_name)
            if collection is None:
                return None
            
            result = collection.insert_one(document)
            print("Inserted document with ID: {}".format(result.inserted_id))
            return result.inserted_id
        except Exception as e:
            print("Error inserting document into {}: {}".format(collection_name, str(e)))
            return None
    
    def insert_documents(self, collection_name, documents):
        """
        Insert multiple documents into a collection
        """
        try:
            collection = self.get_collection(collection_name)
            if collection is None or not documents:
                return []
            
            result = collection.insert_many(documents)
            print("Inserted {} documents into {}".format(len(result.inserted_ids), collection_name))
            return result.inserted_ids
        except Exception as e:
            print("Error inserting documents into {}: {}".format(collection_name, str(e)))
            return []
    
    def find_document(self, collection_name, query):
        """
        Find a single document
        """
        try:
            collection = self.get_collection(collection_name)
            if not collection:
                return None
            return collection.find_one(query)
        except Exception as e:
            print("Error finding document in {}: {}".format(collection_name, str(e)))
            return None
    
    def find_documents(self, collection_name, query=None, limit=None):
        """
        Find multiple documents
        """
        try:
            collection = self.get_collection(collection_name)
            if not collection:
                return []
            
            query = query or {}
            cursor = collection.find(query)
            
            if limit:
                cursor = cursor.limit(limit)
            
            return list(cursor)
        except Exception as e:
            print("Error finding documents in {}: {}".format(collection_name, str(e)))
            return []
    
    def update_document(self, collection_name, query, update_data):
        """
        Update a single document
        """
        try:
            collection = self.get_collection(collection_name)
            if not collection:
                return False
            
            result = collection.update_one(query, {"$set": update_data})
            print("Updated {} document(s) in {}".format(result.modified_count, collection_name))
            return result.modified_count > 0
        except Exception as e:
            print("Error updating document in {}: {}".format(collection_name, str(e)))
            return False
    
    def delete_document(self, collection_name, query):
        """
        Delete a single document
        """
        try:
            collection = self.get_collection(collection_name)
            if not collection:
                return False
            
            result = collection.delete_one(query)
            print("Deleted {} document(s) from {}".format(result.deleted_count, collection_name))
            return result.deleted_count > 0
        except Exception as e:
            print("Error deleting document from {}: {}".format(collection_name, str(e)))
            return False
    
    def delete_all_documents(self, collection_name):
        """
        Delete all documents from a collection
        """
        try:
            collection = self.get_collection(collection_name)
            if collection is None:
                return False
            
            result = collection.delete_many({})
            print("Deleted {} document(s) from {}".format(result.deleted_count, collection_name))
            return True
        except Exception as e:
            print("Error deleting all documents from {}: {}".format(collection_name, str(e)))
            return False
    
    def drop_collection(self, collection_name):
        """
        Drop an entire collection from the database
        """
        try:
            if self.db is None:
                print("Database not initialized")
                return False
            
            self.db.drop_collection(collection_name)
            return True
        except Exception as e:
            print("Error dropping collection {}: {}".format(collection_name, str(e)))
            return False
    
    def list_collections(self):
        """
        List all collections in the database
        """
        try:
            if self.db is None:
                return []
            collections = self.db.list_collection_names()
            print("Collections in database: {}".format(collections))
            return collections
        except Exception as e:
            print("Error listing collections: {}".format(str(e)))
            return []
    
    def create_index(self, collection_name, index_spec):
        """
        Create an index on a collection
        """
        try:
            collection = self.get_collection(collection_name)
            if collection is None:
                return False
            
            result = collection.create_index(index_spec)
            print("Created index '{}' on collection {}".format(result, collection_name))
            return True
        except Exception as e:
            print("Error creating index on {}: {}".format(collection_name, str(e)))
            return False
    
    def close_connection(self):
        """
        Close MongoDB connection
        """
        try:
            if self.client:
                self.client.close()
                print("MongoDB connection closed")
        except Exception as e:
            print("Error closing MongoDB connection: {}".format(str(e)))
