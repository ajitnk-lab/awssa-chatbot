#!/bin/bash

# Deploy Lambda function for AWS Solutions Architect Agent

set -e

echo "🚀 Deploying Lambda function..."

# Get function name from CDK outputs (if available)
FUNCTION_NAME="AwsReposAgentStack-AgentFunction"

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME >/dev/null 2>&1; then
    echo "📦 Updating existing Lambda function: $FUNCTION_NAME"
    
    # Create deployment package
    echo "📦 Creating deployment package..."
    rm -f lambda-deployment.zip
    zip -r lambda-deployment.zip . -x "*.sh" "*.md" "__pycache__/*" "*.pyc"
    
    # Update function code
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://lambda-deployment.zip
    
    echo "✅ Lambda function updated successfully"
else
    echo "❌ Lambda function not found. Please deploy CDK stack first."
    echo "Run: cd ../cdk && npm run deploy"
    exit 1
fi

# Clean up
rm -f lambda-deployment.zip

echo "🎉 Lambda deployment complete!"
