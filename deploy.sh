#!/bin/bash

# AWS Solutions Architect Agent - Master Deployment Script
# Deploys the complete chatbot solution to AWS

set -e

echo "🚀 AWS Solutions Architect Agent - Deployment Starting..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGION="us-west-2"
STACK_NAME="AwsReposAgentStack"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists aws; then
        print_error "AWS CLI not found. Please install AWS CLI."
        exit 1
    fi
    
    if ! command_exists node; then
        print_error "Node.js not found. Please install Node.js."
        exit 1
    fi
    
    if ! command_exists npm; then
        print_error "npm not found. Please install npm."
        exit 1
    fi
    
    if ! command_exists python3; then
        print_error "Python 3 not found. Please install Python 3."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        print_error "AWS credentials not configured. Please run 'aws configure'."
        exit 1
    fi
    
    print_success "All prerequisites met!"
}

# Phase 1: Prepare Data
prepare_data() {
    print_status "Phase 1: Preparing repository data..."
    
    if [ ! -f "classification_results_awslabs.csv" ]; then
        print_error "classification_results_awslabs.csv not found!"
        exit 1
    fi
    
    # Convert CSV to JSON
    python3 scripts/convert_csv_to_json.py
    
    if [ ! -d "data/repos" ] || [ -z "$(ls -A data/repos)" ]; then
        print_error "Data conversion failed!"
        exit 1
    fi
    
    print_success "Data preparation complete! $(ls data/repos | wc -l) repositories processed."
}

# Phase 2: Deploy Infrastructure
deploy_infrastructure() {
    print_status "Phase 2: Deploying AWS infrastructure..."
    
    cd cdk
    
    # Install dependencies
    print_status "Installing CDK dependencies..."
    npm install
    
    # Build TypeScript
    print_status "Building CDK project..."
    npm run build
    
    # Bootstrap CDK (if needed)
    print_status "Bootstrapping CDK..."
    npx cdk bootstrap aws://$(aws sts get-caller-identity --query Account --output text)/$REGION
    
    # Deploy stack
    print_status "Deploying CDK stack..."
    npx cdk deploy --require-approval never --outputs-file ../cdk-outputs.json
    
    cd ..
    
    if [ ! -f "cdk-outputs.json" ]; then
        print_error "CDK deployment failed - no outputs file generated!"
        exit 1
    fi
    
    print_success "Infrastructure deployment complete!"
}

# Phase 3: Upload Data to S3
upload_data() {
    print_status "Phase 3: Uploading repository data to S3..."
    
    # Extract bucket name from CDK outputs
    DATA_BUCKET=$(python3 -c "
import json
with open('cdk-outputs.json', 'r') as f:
    outputs = json.load(f)
    print(outputs['$STACK_NAME']['DataBucketName'])
")
    
    if [ -z "$DATA_BUCKET" ]; then
        print_error "Could not extract data bucket name from CDK outputs!"
        exit 1
    fi
    
    print_status "Uploading to bucket: $DATA_BUCKET"
    
    # Upload JSON files to S3
    aws s3 sync data/repos/ s3://$DATA_BUCKET/repos/ --delete
    
    print_success "Data upload complete!"
}

# Phase 4: Sync Knowledge Base
sync_knowledge_base() {
    print_status "Phase 4: Syncing Bedrock Knowledge Base..."
    
    # Extract Knowledge Base and Data Source IDs
    KB_ID=$(python3 -c "
import json
with open('cdk-outputs.json', 'r') as f:
    outputs = json.load(f)
    print(outputs['$STACK_NAME']['KnowledgeBaseId'])
")
    
    DS_ID=$(python3 -c "
import json
with open('cdk-outputs.json', 'r') as f:
    outputs = json.load(f)
    print(outputs['$STACK_NAME']['DataSourceId'])
")
    
    if [ -z "$KB_ID" ] || [ -z "$DS_ID" ]; then
        print_error "Could not extract Knowledge Base or Data Source ID!"
        exit 1
    fi
    
    print_status "Starting ingestion job for Knowledge Base: $KB_ID"
    
    # Start ingestion job
    JOB_ID=$(aws bedrock-agent start-ingestion-job \
        --knowledge-base-id $KB_ID \
        --data-source-id $DS_ID \
        --region $REGION \
        --query 'ingestionJob.ingestionJobId' \
        --output text)
    
    if [ -z "$JOB_ID" ]; then
        print_error "Failed to start ingestion job!"
        exit 1
    fi
    
    print_status "Ingestion job started: $JOB_ID"
    print_status "Waiting for ingestion to complete..."
    
    # Wait for ingestion to complete
    while true; do
        STATUS=$(aws bedrock-agent get-ingestion-job \
            --knowledge-base-id $KB_ID \
            --data-source-id $DS_ID \
            --ingestion-job-id $JOB_ID \
            --region $REGION \
            --query 'ingestionJob.status' \
            --output text)
        
        case $STATUS in
            "COMPLETE")
                print_success "Knowledge Base sync complete!"
                break
                ;;
            "FAILED")
                print_error "Knowledge Base sync failed!"
                exit 1
                ;;
            "IN_PROGRESS")
                print_status "Ingestion in progress..."
                sleep 30
                ;;
            *)
                print_status "Ingestion status: $STATUS"
                sleep 30
                ;;
        esac
    done
}

# Phase 5: Deploy Lambda Function
deploy_lambda() {
    print_status "Phase 5: Deploying Lambda function..."
    
    cd lambda
    
    # The Lambda function is already deployed by CDK, but we need to update it
    # with the proper dependencies
    
    # Create deployment package
    print_status "Creating Lambda deployment package..."
    rm -f lambda-deployment.zip
    
    # Install dependencies locally
    pip3 install -r requirements.txt -t .
    
    # Create zip file
    zip -r lambda-deployment.zip . -x "*.sh" "*.md" "__pycache__/*" "*.pyc"
    
    # Get function name from CDK outputs
    FUNCTION_NAME=$(python3 -c "
import json
import sys
sys.path.append('..')
with open('../cdk-outputs.json', 'r') as f:
    outputs = json.load(f)
    # Extract function name from ARN or use default
    print('$STACK_NAME-AgentFunction')
")
    
    # Update function code
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://lambda-deployment.zip \
        --region $REGION
    
    # Clean up
    rm -f lambda-deployment.zip
    
    cd ..
    
    print_success "Lambda function deployment complete!"
}

# Phase 6: Deploy Frontend
deploy_frontend() {
    print_status "Phase 6: Deploying frontend..."
    
    # Extract frontend bucket and API URL from CDK outputs
    FRONTEND_BUCKET=$(python3 -c "
import json
with open('cdk-outputs.json', 'r') as f:
    outputs = json.load(f)
    print(outputs['$STACK_NAME']['FrontendBucketName'])
")
    
    API_URL=$(python3 -c "
import json
with open('cdk-outputs.json', 'r') as f:
    outputs = json.load(f)
    print(outputs['$STACK_NAME']['ApiUrl'])
")
    
    if [ -z "$FRONTEND_BUCKET" ] || [ -z "$API_URL" ]; then
        print_error "Could not extract frontend bucket or API URL!"
        exit 1
    fi
    
    # Update API URL in frontend JavaScript
    print_status "Updating API URL in frontend..."
    sed -i.bak "s|https://YOUR_API_GATEWAY_URL|$API_URL|g" frontend/js/api.js
    
    # Upload frontend files to S3
    print_status "Uploading frontend to S3 bucket: $FRONTEND_BUCKET"
    aws s3 sync frontend/ s3://$FRONTEND_BUCKET/ --delete
    
    # Restore original file
    mv frontend/js/api.js.bak frontend/js/api.js
    
    print_success "Frontend deployment complete!"
}

# Phase 7: Display Results
display_results() {
    print_status "Phase 7: Deployment Summary"
    echo "=================================================="
    
    # Extract URLs from CDK outputs
    API_URL=$(python3 -c "
import json
with open('cdk-outputs.json', 'r') as f:
    outputs = json.load(f)
    print(outputs['$STACK_NAME']['ApiUrl'])
")
    
    FRONTEND_URL=$(python3 -c "
import json
with open('cdk-outputs.json', 'r') as f:
    outputs = json.load(f)
    print(outputs['$STACK_NAME']['FrontendUrl'])
")
    
    KB_ID=$(python3 -c "
import json
with open('cdk-outputs.json', 'r') as f:
    outputs = json.load(f)
    print(outputs['$STACK_NAME']['KnowledgeBaseId'])
")
    
    print_success "🎉 Deployment Complete!"
    echo ""
    echo "📊 Resources Created:"
    echo "   • Knowledge Base ID: $KB_ID"
    echo "   • API Gateway URL: $API_URL"
    echo "   • Frontend URL: $FRONTEND_URL"
    echo ""
    echo "🌐 Access your chatbot at: $FRONTEND_URL"
    echo ""
    echo "📝 Next Steps:"
    echo "   1. Test the chatbot interface"
    echo "   2. Monitor costs in AWS Cost Explorer"
    echo "   3. Check CloudWatch logs for any issues"
    echo ""
    echo "💡 Useful Commands:"
    echo "   • View logs: aws logs tail /aws/lambda/$STACK_NAME-AgentFunction --follow"
    echo "   • Check costs: aws ce get-cost-and-usage --time-period Start=\$(date -d '1 month ago' +%Y-%m-%d),End=\$(date +%Y-%m-%d) --granularity MONTHLY --metrics BlendedCost"
    echo ""
}

# Main deployment flow
main() {
    check_prerequisites
    prepare_data
    deploy_infrastructure
    upload_data
    sync_knowledge_base
    deploy_lambda
    deploy_frontend
    display_results
}

# Handle script interruption
trap 'print_error "Deployment interrupted!"; exit 1' INT TERM

# Run main deployment
main

print_success "🚀 AWS Solutions Architect Agent is ready!"
