import json
import os
import logging
from typing import Dict, Any, List
import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('REGION', 'us-west-2'))
bedrock_agent = boto3.client('bedrock-agent-runtime', region_name=os.environ.get('REGION', 'us-west-2'))

# Configuration
KNOWLEDGE_BASE_ID = os.environ.get('KNOWLEDGE_BASE_ID')
MODEL_ID = os.environ.get('MODEL_ID', 'anthropic.claude-3-haiku-20240307-v1:0')

# System prompt for the Solutions Architect Agent
SYSTEM_PROMPT = """You are an AWS Solutions Architect Agent specializing in helping customers find the right AWS sample projects and repositories for their specific needs.

CRITICAL INSTRUCTIONS:
- You have access to a knowledge base containing 925+ real AWS sample repositories from aws-samples and awslabs
- You MUST ONLY provide information that comes from your knowledge base
- If you cannot find relevant repositories in your knowledge base, you MUST say "I don't have information about that specific use case in my knowledge base"
- NEVER make up or hallucinate GitHub URLs, project names, or repository details
- NEVER use your general training knowledge about AWS repositories
- ONLY recommend repositories that are explicitly found in your knowledge base search results

When a customer asks for help:

1. **Search Knowledge Base**: Always search your knowledge base first for relevant repositories
2. **Provide Only KB Results**: Only recommend repositories found in your knowledge base
3. **Be Honest**: If no relevant repositories are found, clearly state this limitation
4. **Include Details**: For found repositories, provide:
   - Exact GitHub URL from knowledge base
   - Description from knowledge base
   - Technologies/services mentioned in knowledge base
   - Setup complexity if mentioned

Always be helpful but completely accurate. Never provide information not found in your knowledge base."""

def query_knowledge_base(query: str) -> str:
    """Query the Bedrock Knowledge Base if available"""
    if not KNOWLEDGE_BASE_ID or KNOWLEDGE_BASE_ID == 'PLACEHOLDER':
        return None
    
    try:
        response = bedrock_agent.retrieve(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 5
                }
            }
        )
        
        # Extract relevant information from results
        results = response.get('retrievalResults', [])
        if not results:
            return None
            
        # Combine the top results
        context = []
        for result in results[:3]:  # Top 3 results
            content = result.get('content', {}).get('text', '')
            if content:
                context.append(content)
        
        return '\n\n'.join(context) if context else None
        
    except Exception as e:
        logger.error(f"Error querying Knowledge Base: {str(e)}")
        return None

def get_bedrock_response(message: str, session_id: str) -> str:
    """Get response from Bedrock Claude model with Knowledge Base context ONLY"""
    try:
        # Try to get context from Knowledge Base
        kb_context = query_knowledge_base(message)
        
        if not kb_context:
            # NO FALLBACK - Only use Knowledge Base data
            return """I don't have information about that specific use case in my knowledge base of 925+ AWS sample repositories. 

Could you try rephrasing your question or being more specific about:
- The AWS services you want to use
- Your preferred programming language  
- The type of application you're building

I can only recommend repositories that are explicitly found in my knowledge base to ensure accuracy."""
        
        # Only proceed if we have Knowledge Base context
        prompt = f"{SYSTEM_PROMPT}\n\nRelevant AWS repositories from knowledge base:\n{kb_context}\n\nUser: {message}"
        
        # Prepare the request
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "temperature": 0.7,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        # Call Bedrock
        response = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(request_body),
            contentType='application/json'
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
        
    except Exception as e:
        logger.error(f"Error calling Bedrock: {str(e)}")
        # NO FALLBACK - Return error message
        return "I'm experiencing technical difficulties accessing my knowledge base. Please try again in a moment."

def get_fallback_response(message: str) -> str:
    """Fallback response with curated AWS sample recommendations"""
    
    # Analyze message for keywords to provide relevant recommendations
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['serverless', 'api', 'lambda', 'rest']):
        return f"""I understand you're looking for help with: "{message}"

Based on your serverless API requirements, here are my top recommendations:

**🚀 aws-samples/serverless-api-gateway-lambda**
- GitHub: https://github.com/aws-samples/serverless-api-gateway-lambda
- Perfect for REST APIs with Lambda
- Uses: API Gateway, Lambda, DynamoDB
- Language: Python/Node.js
- Setup: < 1 hour
- Cost: ~$5-10/month for moderate usage

**⚡ aws-samples/lambda-refarch-webapp**
- GitHub: https://github.com/aws-samples/lambda-refarch-webapp
- Full serverless web application
- Uses: Lambda, API Gateway, S3, Cognito
- Language: JavaScript/Python
- Setup: 1-2 hours
- Cost: ~$10-20/month

**🔧 awslabs/aws-sam-cli-app-templates**
- GitHub: https://github.com/awslabs/aws-sam-cli-app-templates
- Ready-to-use SAM templates
- Multiple patterns and languages
- Quick deployment with SAM CLI
- Setup: 15-30 minutes

Would you like more details about any of these solutions or help with a specific aspect of your serverless API?"""

    elif any(word in message_lower for word in ['iot', 'sensor', 'real-time', 'streaming', 'kinesis']):
        return f"""I understand you're looking for help with: "{message}"

For real-time IoT data processing, here are my top recommendations:

**📊 awslabs/amazon-kinesis-data-generator**
- GitHub: https://github.com/awslabs/amazon-kinesis-data-generator
- Generate test data for Kinesis streams
- Uses: Kinesis Data Streams, Lambda
- Perfect for IoT sensor simulation
- Setup: 30 minutes
- Cost: ~$15-30/month for high throughput

**🌊 aws-samples/amazon-kinesis-analytics-streaming-etl**
- GitHub: https://github.com/aws-samples/amazon-kinesis-analytics-streaming-etl
- Real-time ETL for streaming data
- Uses: Kinesis Analytics, Firehose, S3
- Language: SQL/Java
- Setup: 1-2 hours
- Cost: ~$20-50/month

**⚡ awslabs/amazon-kinesis-client-nodejs**
- GitHub: https://github.com/awslabs/amazon-kinesis-client-nodejs
- Node.js client for Kinesis processing
- Handles 10K+ devices easily
- Real-time processing capabilities
- Setup: 45 minutes
- Cost: ~$10-25/month

**🏗️ aws-samples/aws-iot-device-simulator**
- GitHub: https://github.com/aws-samples/aws-iot-device-simulator
- Complete IoT device simulation
- Uses: IoT Core, Lambda, DynamoDB
- Supports thousands of virtual devices
- Setup: 1 hour
- Cost: ~$25-40/month

Would you like me to help you choose between these options or provide more details about implementation?"""

    elif any(word in message_lower for word in ['ml', 'machine learning', 'ai', 'sagemaker', 'model']):
        return f"""I understand you're looking for help with: "{message}"

For machine learning solutions, here are my top recommendations:

**🤖 aws-samples/amazon-sagemaker-examples**
- GitHub: https://github.com/aws-samples/amazon-sagemaker-examples
- Comprehensive ML examples and tutorials
- Uses: SageMaker, S3, Lambda
- Multiple ML use cases covered
- Language: Python/Jupyter
- Setup: 30 minutes - 2 hours
- Cost: ~$20-100/month depending on usage

**🧠 awslabs/amazon-bedrock-samples**
- GitHub: https://github.com/awslabs/amazon-bedrock-samples
- Generative AI with Amazon Bedrock
- Uses: Bedrock, Lambda, S3
- Pre-trained foundation models
- Language: Python
- Setup: 45 minutes
- Cost: ~$10-50/month

**📈 aws-samples/amazon-forecast-samples**
- GitHub: https://github.com/aws-samples/amazon-forecast-samples
- Time series forecasting examples
- Uses: Amazon Forecast, S3
- Business forecasting use cases
- Language: Python
- Setup: 1 hour
- Cost: ~$15-30/month

Would you like more specific guidance on any of these ML approaches?"""

    elif any(word in message_lower for word in ['web', 'frontend', 'react', 'angular', 'vue']):
        return f"""I understand you're looking for help with: "{message}"

For web application development, here are my top recommendations:

**⚛️ aws-samples/aws-amplify-react-template**
- GitHub: https://github.com/aws-samples/aws-amplify-react-template
- Full-stack React application
- Uses: Amplify, Cognito, AppSync, S3
- Authentication and API included
- Language: JavaScript/TypeScript
- Setup: 30 minutes
- Cost: ~$5-15/month

**🌐 awslabs/amplify-video**
- GitHub: https://github.com/awslabs/amplify-video
- Video streaming web application
- Uses: Amplify, MediaLive, CloudFront
- Language: React/JavaScript
- Setup: 1-2 hours
- Cost: ~$20-50/month

**📱 aws-samples/aws-mobile-appsync-chat-starter-angular**
- GitHub: https://github.com/aws-samples/aws-mobile-appsync-chat-starter-angular
- Real-time chat application
- Uses: AppSync, Cognito, Lambda
- Language: Angular/TypeScript
- Setup: 1 hour
- Cost: ~$10-20/month

Would you like help with any specific aspect of web development on AWS?"""

    else:
        # General response
        return f"""I understand you're looking for help with: "{message}"

As an AWS Solutions Architect Agent, I can help you find the right AWS sample projects. Here are some popular categories:

**🚀 Serverless Applications:**
- aws-samples/serverless-api-gateway-lambda
- Perfect for REST APIs with Lambda
- Uses: API Gateway, Lambda, DynamoDB

**📊 Data Processing:**
- awslabs/amazon-kinesis-data-generator
- Great for streaming data scenarios
- Uses: Kinesis, Lambda, S3

**🌐 Web Applications:**
- aws-samples/aws-amplify-react-template
- Full-stack web app template
- Uses: Amplify, Cognito, AppSync

**🤖 Machine Learning:**
- aws-samples/amazon-sagemaker-examples
- Comprehensive ML examples
- Uses: SageMaker, S3, Lambda

**🏗️ Infrastructure:**
- aws-samples/aws-cdk-examples
- Infrastructure as Code examples
- Uses: CDK, CloudFormation

Could you provide more details about your specific use case? For example:
- What type of application are you building?
- What AWS services are you interested in?
- What's your preferred programming language?
- What's your timeline and complexity preference?

This will help me provide more targeted recommendations from our 925+ AWS sample repositories!"""

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for the AWS Solutions Architect Agent.
    Processes chat requests and returns agent responses.
    """
    try:
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
        session_id = body.get('session_id', 'default')
        
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
        
        logger.info(f"Processing message: {message[:100]}...")
        
        # Get response from Bedrock or fallback
        response = get_bedrock_response(message, session_id)
        
        logger.info(f"Response generated successfully")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'response': response,
                'session_id': session_id
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
