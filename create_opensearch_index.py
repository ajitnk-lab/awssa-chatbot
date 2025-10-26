#!/usr/bin/env python3
import boto3
import json
import requests
from requests_aws4auth import AWS4Auth

# Get AWS credentials
session = boto3.Session()
credentials = session.get_credentials()
region = 'us-west-2'
service = 'aoss'

# Create AWS4Auth object
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    region,
    service,
    session_token=credentials.token
)

# OpenSearch endpoint
host = 'https://ky9tli1726gu63vj7cw9.us-west-2.aoss.amazonaws.com'
index_name = 'bedrock-knowledge-base-default-index'
url = f'{host}/{index_name}'

# Index configuration
index_config = {
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 512
        }
    },
    "mappings": {
        "properties": {
            "bedrock-knowledge-base-default-vector": {
                "type": "knn_vector",
                "dimension": 1024,
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "faiss"
                }
            },
            "AMAZON_BEDROCK_TEXT_CHUNK": {
                "type": "text"
            },
            "AMAZON_BEDROCK_METADATA": {
                "type": "text"
            }
        }
    }
}

# Delete existing index first
try:
    delete_response = requests.delete(
        url,
        auth=awsauth,
        headers={'Content-Type': 'application/json'}
    )
    print(f"Delete Status: {delete_response.status_code}")
except:
    print("Index doesn't exist or couldn't delete, continuing...")

# Create the index
try:
    response = requests.put(
        url,
        auth=awsauth,
        json=index_config,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Index created successfully!")
    else:
        print("❌ Failed to create index")
        
except Exception as e:
    print(f"Error: {e}")
