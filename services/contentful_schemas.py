from services.contentful_base import ContentfulClient

class ContentfulSchemasService:
    def __init__(self):
        self.client = ContentfulClient()
    
    def get_all_content_types(self):
        """
        Get all content types from Contentful
        """
        return self.client.make_request("content_types").get("items", [])
