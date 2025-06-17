import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentfulClient:
    def __init__(self):
        self.space_id = os.getenv("CONTENTFUL_SPACE_ID")
        self.environment_id = os.getenv("CONTENTFUL_ENVIRONMENT_ID", "staging-2025-05-27")
        self.cma_token = os.getenv("CONTENTFUL_CMA_TOKEN")
        self.base_url = f"https://api.contentful.com/spaces/{self.space_id}/environments/{self.environment_id}"
        self.headers = {
            "Authorization": f"Bearer {self.cma_token}",
            "Content-Type": "application/vnd.contentful.management.v1+json"
        }
    
    def make_request(self, endpoint, params=None):
        """
        Make a GET request to Contentful API
        """
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_paginated_data(self, endpoint, limit=1000, skip=0):
        """
        Get paginated data from Contentful API
        """
        params = {
            "limit": limit,
            "skip": skip
        }
        
        data = self.make_request(endpoint, params)
        items = data.get("items", [])
        total = data.get("total", 0)
        
        logger.info(f"Fetched {len(items)} items from {endpoint} (skip: {skip}, total: {total})")
        
        return items, total
    
    def get_all_paginated_data(self, endpoint, limit=1000):
        """
        Get all data from a paginated endpoint
        """
        all_items = []
        skip = 0
        
        while True:
            items, total = self.get_paginated_data(endpoint, limit=limit, skip=skip)
            all_items.extend(items)
            
            if skip + len(items) >= total:
                break
                
            skip += limit
        
        logger.info(f"Fetched total {len(all_items)} items from {endpoint}")
        return all_items
