#!/usr/bin/env python3
import boto3
import json
import os

s3 = boto3.client('s3')
bucket = 'aws-repos-data-039920874011-us-west-2'

def convert_file(key):
    try:
        # Download file
        response = s3.get_object(Bucket=bucket, Key=key)
        data = json.loads(response['Body'].read())
        
        # Convert to Bedrock format
        bedrock_format = {
            "text": data.get("searchable_content", ""),
            "metadata": {
                "repository": data.get("repository", ""),
                "url": data.get("url", "")
            }
        }
        
        # Upload converted file
        new_key = key.replace('repos/', 'repos_bedrock/')
        s3.put_object(
            Bucket=bucket,
            Key=new_key,
            Body=json.dumps(bedrock_format),
            ContentType='application/json'
        )
        print(f"✅ Converted: {key}")
        return True
        
    except Exception as e:
        print(f"❌ Failed: {key} - {e}")
        return False

def main():
    # List all JSON files
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket, Prefix='repos/')
    
    converted = 0
    failed = 0
    
    for page in pages:
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                if key.endswith('.json'):
                    if convert_file(key):
                        converted += 1
                    else:
                        failed += 1
    
    print(f"\n📊 Results: {converted} converted, {failed} failed")

if __name__ == "__main__":
    main()
