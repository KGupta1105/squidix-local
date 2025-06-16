#!/usr/bin/env python3

import os
import click
from dotenv import load_dotenv
from core.transformer import transform_content_type
from services.squidex import push_schema_to_squidex, get_schema_id_map
from services.contentful import get_all_content_types

load_dotenv()

@click.command()
@click.option("--push", is_flag=True, help="Push schemas to Squidex after transformation")
def migrate(push):
    content_types = get_all_content_types()
    transformed_schemas = []

    schema_id_map = get_schema_id_map()

    for ct in content_types:
        schema = transform_content_type(ct, schema_id_map, resolve_references=False)
        transformed_schemas.append((ct, schema))

        if push:
            push_schema_to_squidex(schema)

    schema_id_map = get_schema_id_map()

    for ct, _ in transformed_schemas:
        schema = transform_content_type(ct, schema_id_map, resolve_references=True)
        if push:
            push_schema_to_squidex(schema)

    print("Migration complete.")

if __name__ == "__main__":
    migrate()