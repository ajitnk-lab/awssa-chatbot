import json
import os
import logging
from typing import Dict, Any
import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Simple Lambda handler for testing the chatbot without Knowledge Base.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': ''
            }
        
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        message = body.get('message', '')
        
        if not message:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps({'error': 'Message is required'})
            }
        
        # Simple mock response for testing
        mock_response = f"""I understand you're looking for help with: "{message}"

As an AWS Solutions Architect Agent, I can help you find the right AWS sample projects. Here are some recommendations:

**For Serverless APIs:**
- aws-samples/serverless-api-gateway-lambda
  - Perfect for REST APIs with Lambda
  - Uses: API Gateway, Lambda, DynamoDB
  - Language: Python/Node.js
  - Setup: < 1 hour

**For Data Processing:**
- awslabs/amazon-kinesis-data-generator
  - Great for streaming data scenarios
  - Uses: Kinesis, Lambda, S3
  - Real-time processing capabilities

**For Web Applications:**
- aws-samples/aws-amplify-react-template
  - Full-stack web app template
  - Uses: Amplify, Cognito, AppSync
  - Frontend: React

Note: This is a test response. The full Knowledge Base integration is being configured to provide more accurate recommendations based on your specific requirements.

Would you like me to help you with any specific AWS service or use case?"""
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'response': mock_response,
                'session_id': 'test-session'
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
