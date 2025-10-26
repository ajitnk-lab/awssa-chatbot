#!/bin/bash

# Sync Bedrock Knowledge Base with updated data

set -e

REGION="us-west-2"
STACK_NAME="AwsReposAgentStack"

echo "🔄 Syncing Bedrock Knowledge Base..."

# Check if CDK outputs exist
if [ ! -f "cdk-outputs.json" ]; then
    echo "❌ CDK outputs not found. Please deploy infrastructure first."
    exit 1
fi

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
    echo "❌ Could not extract Knowledge Base or Data Source ID!"
    exit 1
fi

echo "📊 Knowledge Base ID: $KB_ID"
echo "📊 Data Source ID: $DS_ID"

# Start ingestion job
echo "🚀 Starting ingestion job..."
JOB_ID=$(aws bedrock-agent start-ingestion-job \
    --knowledge-base-id $KB_ID \
    --data-source-id $DS_ID \
    --region $REGION \
    --query 'ingestionJob.ingestionJobId' \
    --output text)

if [ -z "$JOB_ID" ]; then
    echo "❌ Failed to start ingestion job!"
    exit 1
fi

echo "✅ Ingestion job started: $JOB_ID"
echo "⏳ Waiting for completion..."

# Monitor ingestion progress
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
            echo "✅ Knowledge Base sync complete!"
            break
            ;;
        "FAILED")
            echo "❌ Knowledge Base sync failed!"
            
            # Get failure reason
            FAILURE_REASON=$(aws bedrock-agent get-ingestion-job \
                --knowledge-base-id $KB_ID \
                --data-source-id $DS_ID \
                --ingestion-job-id $JOB_ID \
                --region $REGION \
                --query 'ingestionJob.failureReasons' \
                --output text)
            
            echo "Failure reason: $FAILURE_REASON"
            exit 1
            ;;
        "IN_PROGRESS")
            echo "⏳ Ingestion in progress..."
            sleep 30
            ;;
        *)
            echo "📊 Status: $STATUS"
            sleep 30
            ;;
    esac
done

echo "🎉 Knowledge Base sync completed successfully!"
