#!/usr/bin/env python3

import os
import click
from dotenv import load_dotenv
from core.transformer import transform_content_type
from services.squidex import push_schema_to_squidex, get_schema_id_map
from services.contentful import get_all_content_types

load_dotenv()

@click.command()
def migrate():
    content_types = get_all_content_types()
    transformed_schemas = []

    print(f"Found {len(content_types)} content types in Contentful")
    
    schema_id_map = get_schema_id_map()

    for ct in content_types:
        print(f"Processing content type: {ct.get('name', 'Unknown')}")
        schema = transform_content_type(ct, schema_id_map, resolve_references=False)
        transformed_schemas.append((ct, schema))
        push_schema_to_squidex(schema)

    schema_id_map = get_schema_id_map()

    for ct, _ in transformed_schemas:
        print(f"Processing references for: {ct.get('name', 'Unknown')}")
        schema = transform_content_type(ct, schema_id_map, resolve_references=True)
        push_schema_to_squidex(schema)

    print("Migration complete - all schemas pushed to Squidex.")

if __name__ == "__main__":
    migrate()
