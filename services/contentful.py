# Legacy compatibility wrapper - imports from the new modular services
from services.contentful_schemas import ContentfulSchemasService

# Create service instance
_schemas_service = ContentfulSchemasService()

def get_all_content_types():
    """
    Legacy function for backward compatibility
    """
    return _schemas_service.get_all_content_types()
