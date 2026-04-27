#!/usr/bin/env python
"""
Sync static files to Cloudflare R2 bucket
Uses boto3 (already installed) instead of AWS CLI
"""
import os
import sys
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

# Get R2 configuration from environment
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL')

if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME, AWS_S3_ENDPOINT_URL]):
    print("❌ Missing R2 credentials in environment")
    sys.exit(1)

# Create S3 client for R2
s3_client = boto3.client(
    's3',
    endpoint_url=AWS_S3_ENDPOINT_URL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name='auto'
)

# Sync local staticfiles to R2
static_dir = Path('/app/staticfiles')
if not static_dir.exists():
    print(f"❌ Static files directory not found: {static_dir}")
    sys.exit(1)

print(f"📤 Syncing files from {static_dir} to R2...")

uploaded = 0
skipped = 0
errors = 0

# Walk through all files in staticfiles
for file_path in static_dir.rglob('*'):
    if file_path.is_file():
        # Skip unwanted files
        if file_path.suffix == '.pyc' or '__pycache__' in str(file_path) or file_path.name == '.DS_Store':
            continue

        # Get relative path for S3 key
        relative_path = file_path.relative_to(static_dir)
        s3_key = f"static/{relative_path}"

        try:
            # Check if file exists in R2 and compare size
            file_size = file_path.stat().st_size
            try:
                head = s3_client.head_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=s3_key)
                if head['ContentLength'] == file_size:
                    skipped += 1
                    continue
            except ClientError:
                pass  # File doesn't exist in R2, upload it

            # Upload file
            with open(file_path, 'rb') as f:
                s3_client.put_object(
                    Bucket=AWS_STORAGE_BUCKET_NAME,
                    Key=s3_key,
                    Body=f,
                    ACL='public-read'
                )
            uploaded += 1
            print(f"   ✓ {s3_key}")

        except Exception as e:
            errors += 1
            print(f"   ✗ {s3_key}: {e}")

print(f"\n✅ Sync complete:")
print(f"   Uploaded: {uploaded} files")
print(f"   Skipped: {skipped} files (unchanged)")
if errors > 0:
    print(f"   Errors: {errors} files")
    sys.exit(1)
