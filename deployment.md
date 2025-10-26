# AWS Solutions Architect Agent - Deployment Guide

## Prerequisites

### AWS Account Setup
- ✅ AWS Account with Free Tier credits
- ✅ AWS CLI installed and configured
- ✅ AWS credentials configured (`aws configure`)
- ✅ Region set to `us-west-2`

### Bedrock Access
- ✅ Enable model access in Bedrock console:
  - Claude 3 Haiku (`anthropic.claude-3-haiku-20240307-v1:0`)
  - Titan Text Embeddings v2 (`amazon.titan-embed-text-v2:0`)
- ✅ OpenSearch Serverless access (available in us-west-2)

### Development Tools
- ✅ Node.js 18+ (for CDK)
- ✅ Python 3.12+ (for Lambda)
- ✅ AWS CDK CLI: `npm install -g aws-cdk`
- ✅ Git

### Data File
- ✅ `classification_results_awslabs.csv` in project directory

---

## Deployment Steps

### Phase 1: Data Preparation

#### Step 1.1: Convert CSV to JSON

Create `scripts/convert_csv_to_json.py`:

```python
#!/usr/bin/env python3
import csv
import json
import os

def convert_csv_to_json(csv_file, output_dir):
    """Convert CSV to JSON documents for KB ingestion"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Create searchable content
            searchable_content = f"""
{row['repository']}
{row.get('description', '')}
Solution Type: {row['solution_type']}
Technical Competency: {row['technical_competencies']}
Customer Problems: {row['customer_problems']}
AWS Services: {row['aws_services']}
Primary Language: {row['primary_language']}
Setup Time: {row['setup_time']}
Cost Range: {row['cost_range']}
GenAI/Agentic: {row['genai_agentic']}
            """.strip()
            
            # Create document with Bedrock format
            doc = {
                "text": searchable_content,
                "metadata": {
                    "repository": row['repository'],
                    "url": row['url'],
                    "description": row.get('description', ''),
                    "solution_type": row['solution_type'],
                    "technical_competencies": row['technical_competencies'],
                    "aws_services": row['aws_services'],
                    "customer_problems": row['customer_problems'],
                    "primary_language": row['primary_language'],
                    "setup_time": row['setup_time'],
                    "cost_range": row['cost_range'],
                    "stars": row.get('stars', 0),
                    "genai_agentic": row['genai_agentic']
                }
            }
            
            # Save to file
            filename = row['repository'].replace('/', '-') + '.json'
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as out:
                json.dump(doc, out, indent=2)
    
    print(f"✅ Converted {len(os.listdir(output_dir))} repos to JSON")

if __name__ == '__main__':
    convert_csv_to_json(
        'classification_results_awslabs.csv',
        'data/repos'
    )
```

Run the script:
```bash
python3 scripts/convert_csv_to_json.py
```

This will create files in the proper Bedrock format with "text" and "metadata" fields.

Expected output:
```
✅ Converted 925 repos to JSON
```

---

#### Step 1.2: Upload Data to S3

Create S3 bucket and upload data:

```bash
# Create bucket (replace with unique name)
BUCKET_NAME="aws-repos-data-$(date +%s)"
aws s3 mb s3://${BUCKET_NAME} --region us-west-2

# Upload JSON files to repos_bedrock/ prefix for proper Bedrock format
aws s3 sync data/repos/ s3://${BUCKET_NAME}/repos_bedrock/ --region us-west-2

# Verify upload
aws s3 ls s3://${BUCKET_NAME}/repos_bedrock/ --recursive | wc -l
# Should show 925
```

Save bucket name for later:
```bash
echo $BUCKET_NAME > .bucket-name
```

---

### Phase 2: Infrastructure Deployment

#### Step 2.1: Initialize CDK Project

```bash
# Create CDK project
mkdir cdk
cd cdk

# Initialize TypeScript CDK project
cdk init app --language typescript

# Install dependencies
npm install @aws-cdk/aws-bedrock-alpha \
            @aws-cdk/aws-opensearchserverless \
            @aws-cdk/aws-s3 \
            @aws-cdk/aws-lambda \
            @aws-cdk/aws-apigateway \
            @aws-cdk/aws-cloudfront \
            @aws-cdk/aws-iam
```

---

#### Step 2.2: Create CDK Stack

Edit `lib/cdk-stack.ts`:

```typescript
import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as opensearchserverless from 'aws-cdk-lib/aws-opensearchserverless';
import * as bedrock from '@aws-cdk/aws-bedrock-alpha';
import { Construct } from 'constructs';

export class AwsReposAgentStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Get data bucket name from context
    const dataBucketName = this.node.tryGetContext('dataBucketName');
    const dataBucket = s3.Bucket.fromBucketName(this, 'DataBucket', dataBucketName);

    // Create OpenSearch Serverless collection
    const collection = new opensearchserverless.CfnCollection(this, 'VectorCollection', {
      name: 'aws-repos-vectors',
      type: 'VECTORSEARCH'
    });

    // IAM role for Knowledge Base
    const kbRole = new iam.Role(this, 'KBRole', {
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonBedrockFullAccess')
      ]
    });

    // Grant KB access to data bucket and OpenSearch collection
    dataBucket.grantRead(kbRole);

    // Create Knowledge Base with OpenSearch Serverless
    const knowledgeBase = new bedrock.CfnKnowledgeBase(this, 'RepoKB', {
      name: 'aws-repos-knowledge-base',
      roleArn: kbRole.roleArn,
      knowledgeBaseConfiguration: {
        type: 'VECTOR',
        vectorKnowledgeBaseConfiguration: {
          embeddingModelArn: `arn:aws:bedrock:${this.region}::foundation-model/amazon.titan-embed-text-v2:0`,
          embeddingModelConfiguration: {
            bedrockEmbeddingModelConfiguration: {
              dimensions: 1024
            }
          }
        }
      },
      storageConfiguration: {
        type: 'OPENSEARCH_SERVERLESS',
        opensearchServerlessConfiguration: {
          collectionArn: collection.attrArn,
          vectorIndexName: 'bedrock-knowledge-base-default-index',
          fieldMapping: {
            vectorField: 'bedrock-knowledge-base-default-vector',
            textField: 'AMAZON_BEDROCK_TEXT_CHUNK',
            metadataField: 'AMAZON_BEDROCK_METADATA'
          }
        }
      }
    });

    // Create Data Source
    const dataSource = new bedrock.CfnDataSource(this, 'RepoDataSource', {
      knowledgeBaseId: knowledgeBase.attrKnowledgeBaseId,
      name: 'aws-repos-data-source',
      dataSourceConfiguration: {
        type: 'S3',
        s3Configuration: {
          bucketArn: dataBucket.bucketArn,
          inclusionPrefixes: ['repos_bedrock/']  // Use Bedrock format files
        }
      }
    });

    // Lambda execution role
    const lambdaRole = new iam.Role(this, 'LambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole')
      ]
    });

    // Grant Lambda access to Bedrock
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        'bedrock:InvokeModel',
        'bedrock:Retrieve'
      ],
      resources: ['*']
    }));

    // Lambda function
    const agentFunction = new lambda.Function(this, 'AgentFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'lambda_function.lambda_handler',
      code: lambda.Code.fromAsset('../lambda'),
      role: lambdaRole,
      timeout: cdk.Duration.seconds(30),
      memorySize: 1024,
      environment: {
        KB_ID: knowledgeBase.attrKnowledgeBaseId,
        AWS_REGION: this.region
      }
    });

    // API Gateway
    const api = new apigateway.RestApi(this, 'AgentAPI', {
      restApiName: 'AWS Repos Agent API',
      description: 'API for AWS Solutions Architect Agent',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'Authorization']
      }
    });

    // API endpoint
    const chat = api.root.addResource('chat');
    chat.addMethod('POST', new apigateway.LambdaIntegration(agentFunction), {
      apiKeyRequired: false
    });

    // S3 bucket for frontend
    const frontendBucket = new s3.Bucket(this, 'FrontendBucket', {
      bucketName: `aws-repos-frontend-${this.account}`,
      websiteIndexDocument: 'index.html',
      publicReadAccess: true,
      blockPublicAccess: new s3.BlockPublicAccess({
        blockPublicAcls: false,
        blockPublicPolicy: false,
        ignorePublicAcls: false,
        restrictPublicBuckets: false
      }),
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true
    });

    // Outputs
    new cdk.CfnOutput(this, 'CollectionArn', {
      value: collection.attrArn,
      description: 'OpenSearch Serverless Collection ARN'
    });

    new cdk.CfnOutput(this, 'KnowledgeBaseId', {
      value: knowledgeBase.attrKnowledgeBaseId,
      description: 'Bedrock Knowledge Base ID'
    });

    new cdk.CfnOutput(this, 'DataSourceId', {
      value: dataSource.attrDataSourceId,
      description: 'Data Source ID'
    });

    new cdk.CfnOutput(this, 'ApiUrl', {
      value: api.url,
      description: 'API Gateway URL'
    });

    new cdk.CfnOutput(this, 'FrontendUrl', {
      value: frontendBucket.bucketWebsiteUrl,
      description: 'Frontend URL'
    });
  }
}
```

---

#### Step 2.3: Deploy Infrastructure

```bash
# Bootstrap CDK (first time only)
cdk bootstrap aws://ACCOUNT-ID/us-west-2

# Set data bucket name
BUCKET_NAME=$(cat ../.bucket-name)
export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export CDK_DEFAULT_REGION=us-west-2

# Deploy stack
cdk deploy \
  --context dataBucketName=$BUCKET_NAME \
  --require-approval never

# Save outputs
cdk deploy --outputs-file outputs.json
```

Expected output:
```
✅ AwsReposAgentStack

Outputs:
AwsReposAgentStack.CollectionArn = arn:aws:aoss:us-west-2:123456789012:collection/xxxxx
AwsReposAgentStack.KnowledgeBaseId = TOJENJXGHW
AwsReposAgentStack.DataSourceId = NRTZFOH2YX
AwsReposAgentStack.ApiUrl = https://xxxxx.execute-api.us-west-2.amazonaws.com/prod/
AwsReposAgentStack.FrontendUrl = http://aws-repos-frontend-xxxxx.s3-website-us-west-2.amazonaws.com
```

---

### Phase 3: Knowledge Base Sync

#### Step 3.1: Create OpenSearch Index

Before syncing data, create the proper OpenSearch index:

```bash
# Create index creation script
python3 create_opensearch_index.py

# This creates the index with proper FAISS configuration
```

#### Step 3.2: Sync Data Source

```bash
# Get IDs from outputs
KB_ID=$(jq -r '.AwsReposAgentStack.KnowledgeBaseId' outputs.json)
DS_ID=$(jq -r '.AwsReposAgentStack.DataSourceId' outputs.json)

# Start ingestion job
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id $KB_ID \
  --data-source-id $DS_ID \
  --region us-west-2

# Check status
aws bedrock-agent get-ingestion-job \
  --knowledge-base-id $KB_ID \
  --data-source-id $DS_ID \
  --ingestion-job-id INGESTION_JOB_ID \
  --region us-west-2
```

Wait for status to be `COMPLETE` (10-30 minutes for 925 repos).

Monitor progress:
```bash
python3 monitor_ingestion.py
```

---

### Phase 4: Lambda Function Deployment

#### Step 4.1: Create Lambda Code

Create `lambda/lambda_function.py`:

```python
import json
import os
import uuid
import time
from strands import Agent
from strands_tools import retrieve

# System prompt
SYSTEM_PROMPT = """
You are an expert AWS Solutions Architect helping customers find the right 
AWS sample projects from GitHub for their specific needs.

Your approach:
1. UNDERSTAND: Ask 2-3 clarifying questions to understand their needs
2. SEARCH: Use the retrieve tool to query the knowledge base
3. RECOMMEND: Provide 2-3 most relevant repositories with explanations
4. REFINE: Ask if they need more details or alternatives

Guidelines:
- Be conversational and helpful
- Explain why each recommendation fits
- Provide GitHub URLs
- Keep responses concise but informative
"""

# Initialize agent (outside handler for reuse)
agent = Agent(
    system_prompt=SYSTEM_PROMPT,
    tools=[retrieve],
    model_provider='bedrock',
    model_config={
        'model_id': 'anthropic.claude-3-haiku-20240307-v1:0',
        'region': os.environ.get('AWS_REGION', 'us-west-2'),
        'max_tokens': 4096,
        'temperature': 0.7
    },
    tool_config={
        'retrieve': {
            'knowledge_base_id': os.environ['KB_ID'],
            'max_results': 10,
            'min_score': 0.5
        }
    }
)

# In-memory conversation storage
conversations = {}

def lambda_handler(event, context):
    """Handle chat requests"""
    try:
        # Parse request
        body = json.loads(event['body'])
        message = body['message']
        session_id = body.get('session_id', str(uuid.uuid4()))
        
        # Get or create conversation
        if session_id not in conversations:
            conversations[session_id] = {
                'history': [],
                'created_at': time.time()
            }
        
        conversation = conversations[session_id]
        
        # Add user message
        conversation['history'].append({
            'role': 'user',
            'content': message
        })
        
        # Build context (last 5 messages)
        context = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in conversation['history'][-5:]
        ])
        
        # Query agent
        response = agent(context if len(conversation['history']) > 1 else message)
        
        # Add assistant response
        conversation['history'].append({
            'role': 'assistant',
            'content': response
        })
        
        # Return response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'response': response,
                'session_id': session_id
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
```

---

#### Step 4.2: Create Requirements File

Create `lambda/requirements.txt`:

```
strands-agents==0.1.10
strands-agents-tools==0.1.5
boto3>=1.34.0
```

---

#### Step 4.3: Package and Deploy Lambda

```bash
cd lambda

# Create package directory
mkdir -p package

# Install dependencies
pip install -r requirements.txt -t package/

# Copy Lambda code
cp lambda_function.py package/

# Create deployment package
cd package
zip -r ../lambda-deployment.zip .
cd ..

# Update Lambda function
aws lambda update-function-code \
  --function-name AwsReposAgentStack-AgentFunction \
  --zip-file fileb://lambda-deployment.zip \
  --region us-west-2

# Wait for update to complete
aws lambda wait function-updated \
  --function-name AwsReposAgentStack-AgentFunction \
  --region us-west-2

echo "✅ Lambda function deployed"
```

---

### Phase 5: Frontend Deployment

#### Step 5.1: Create Frontend Files

Create `frontend/index.html`, `frontend/css/style.css`, `frontend/js/api.js`, `frontend/js/ui.js`, `frontend/js/app.js` (see design.md for code).

Update API URL in `frontend/js/app.js`:
```javascript
const API_URL = 'YOUR_API_GATEWAY_URL_FROM_OUTPUTS';
```

---

#### Step 5.2: Deploy Frontend

```bash
cd frontend

# Get frontend bucket name
FRONTEND_BUCKET=$(jq -r '.AwsReposAgentStack.FrontendUrl' ../cdk/outputs.json | sed 's|http://||' | sed 's|.s3-website.*||')

# Upload files
aws s3 sync . s3://${FRONTEND_BUCKET}/ --region us-west-2

# Verify
aws s3 ls s3://${FRONTEND_BUCKET}/

echo "✅ Frontend deployed"
```

---

### Phase 6: Testing

#### Step 6.1: Test API Endpoint

```bash
API_URL=$(jq -r '.AwsReposAgentStack.ApiUrl' cdk/outputs.json)

curl -X POST ${API_URL}chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need a serverless API solution",
    "session_id": "test-123"
  }'
```

Expected response:
```json
{
  "response": "I can help you with that! ...",
  "session_id": "test-123"
}
```

---

#### Step 6.2: Test Web Interface

```bash
FRONTEND_URL=$(jq -r '.AwsReposAgentStack.FrontendUrl' cdk/outputs.json)
echo "Open in browser: $FRONTEND_URL"
```

Test queries:
1. "I need a serverless API"
2. "How do I process streaming data?"
3. "I want to implement ML model deployment"

---

### Phase 7: Monitoring Setup

#### Step 7.1: Create Billing Alert

```bash
# Create SNS topic
aws sns create-topic \
  --name billing-alerts \
  --region us-east-1

# Subscribe email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT-ID:billing-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com \
  --region us-east-1

# Create billing alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "AWS-Billing-Alert-50USD" \
  --alarm-description "Alert when AWS charges exceed $50" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold 50 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT-ID:billing-alerts \
  --region us-east-1
```

---

#### Step 7.2: Create CloudWatch Dashboard

```bash
aws cloudwatch put-dashboard \
  --dashboard-name AWS-Repos-Agent \
  --dashboard-body file://dashboard.json \
  --region us-west-2
```

Create `dashboard.json`:
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Invocations", {"stat": "Sum"}],
          [".", "Errors", {"stat": "Sum"}],
          [".", "Duration", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-west-2",
        "title": "Lambda Metrics"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ApiGateway", "Count", {"stat": "Sum"}],
          [".", "4XXError", {"stat": "Sum"}],
          [".", "5XXError", {"stat": "Sum"}]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-west-2",
        "title": "API Gateway Metrics"
      }
    }
  ]
}
```

---

## Post-Deployment Verification

### Checklist

- [ ] Knowledge Base sync completed successfully
- [ ] Lambda function responds to test requests
- [ ] API Gateway endpoint is accessible
- [ ] Web chatbot loads and displays UI
- [ ] Can send messages and receive responses
- [ ] Recommendations include GitHub URLs
- [ ] Billing alert is configured
- [ ] CloudWatch logs are being generated

---

## Troubleshooting

### Issue: Knowledge Base Sync Fails

**Symptoms**: Ingestion job status is `FAILED`

**Solutions**:
1. Check IAM permissions for KB role
2. Verify S3 bucket access
3. Check JSON file format
4. Review CloudWatch logs

```bash
aws logs tail /aws/bedrock/knowledgebases/$KB_ID --follow
```

---

### Issue: Lambda Timeout

**Symptoms**: API returns 504 Gateway Timeout

**Solutions**:
1. Increase Lambda timeout (max 30s for API Gateway)
2. Reduce KB max_results
3. Optimize agent prompt
4. Check Bedrock service status

```bash
aws lambda update-function-configuration \
  --function-name AwsReposAgentStack-AgentFunction \
  --timeout 30 \
  --region us-west-2
```

---

### Issue: CORS Errors

**Symptoms**: Browser console shows CORS errors

**Solutions**:
1. Verify API Gateway CORS configuration
2. Check Lambda response headers
3. Clear browser cache

```bash
# Update API Gateway CORS
aws apigateway update-rest-api \
  --rest-api-id YOUR_API_ID \
  --patch-operations op=replace,path=/cors/allowOrigins,value='*'
```

---

### Issue: High Costs

**Symptoms**: Billing alert triggered

**Solutions**:
1. Check CloudWatch metrics for usage
2. Review Lambda invocation count
3. Check Bedrock API calls
4. Reduce max_tokens in agent config

```bash
# Check costs
aws ce get-cost-and-usage \
  --time-period Start=2025-10-01,End=2025-10-31 \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=SERVICE
```

---

## Cleanup

### Remove All Resources

```bash
# Delete CDK stack
cd cdk
cdk destroy --force

# Delete S3 buckets (if not auto-deleted)
aws s3 rb s3://$BUCKET_NAME --force
aws s3 rb s3://$FRONTEND_BUCKET --force

# Delete CloudWatch logs
aws logs delete-log-group \
  --log-group-name /aws/lambda/AwsReposAgentStack-AgentFunction \
  --region us-west-2

echo "✅ All resources deleted"
```

---

## Cost Summary

### One-Time Costs
- Knowledge Base creation: $5-10
- Embeddings (925 repos): $5-10
- **Total**: $10-20

### Monthly Costs (1000 queries)
- S3 Vector storage: $1-2
- Lambda invocations: $0.20-1
- Bedrock LLM calls: $5-10
- API Gateway: $0.10-0.50
- S3 + CloudFront: $0.50-1
- **Total**: $7-15/month

### Total First Month
- Setup + 1 month: $17-35

---

## Next Steps

1. ✅ Test with real user scenarios
2. ✅ Monitor costs daily for first week
3. ✅ Collect user feedback
4. ✅ Iterate on agent prompts
5. ✅ Improve metadata quality (separate project)
6. ✅ Add authentication (if needed)
7. ✅ Implement conversation persistence (if needed)

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-26  
**Status**: Ready for Deployment
