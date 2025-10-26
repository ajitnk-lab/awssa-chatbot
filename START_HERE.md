# 🚀 START HERE - Implementation Guide

## Quick Start Prompt for AI Assistant

Copy and paste this prompt to your AI assistant (Claude, ChatGPT, Amazon Q, etc.) to start building the project:

---

## **IMPLEMENTATION PROMPT**

```
I want to build the AWS Solutions Architect Agent Chatbot based on the complete 
documentation in this repository.

PROJECT CONTEXT:
- Repository: https://github.com/ajitnk-lab/awssa-chatbot
- Documentation: requirements.md, design.md, deployment.md
- Goal: Build an AI chatbot that helps users find AWS sample projects
- Tech Stack: Bedrock, Strands Agents, Lambda, S3 Vectors, CDK

WHAT I NEED YOU TO DO:

Phase 1: Data Preparation
1. Create scripts/convert_csv_to_json.py to convert CSV to JSON documents
2. The script should read classification_results_awslabs.csv (925 repos)
3. Create enriched JSON documents with searchable content
4. Output to data/repos/ directory

Phase 2: CDK Infrastructure
1. Initialize CDK TypeScript project in cdk/ directory
2. Create lib/cdk-stack.ts with:
   - S3 buckets (data, vectors, frontend)
   - Bedrock Knowledge Base with S3 Vectors
   - Data Source configuration
   - Lambda function
   - API Gateway REST API
   - IAM roles and permissions
3. Follow the exact design from design.md

Phase 3: Lambda Function
1. Create lambda/lambda_function.py with Strands Agent
2. Create lambda/requirements.txt with dependencies
3. Implement conversation state management
4. Use system prompt from design.md
5. Configure retrieve tool for KB queries

Phase 4: Frontend
1. Create frontend/index.html with chat interface
2. Create frontend/css/style.css with styling
3. Create frontend/js/api.js for API calls
4. Create frontend/js/ui.js for UI management
5. Create frontend/js/app.js for main logic

Phase 5: Deployment Scripts
1. Create deploy.sh for automated deployment
2. Create scripts for KB sync
3. Add monitoring setup scripts

IMPORTANT CONSTRAINTS:
- AWS Region: us-west-2
- Use Claude 3 Haiku (cost-optimized)
- Use S3 Vectors (not OpenSearch)
- Stay within Free Tier budget ($100-200 credits)
- Follow exact architecture from design.md

START WITH:
Create the data conversion script (scripts/convert_csv_to_json.py) first.
Make it production-ready with error handling and logging.

Let's build this step by step. Ready to start?
```

---

## **Alternative: Step-by-Step Prompts**

If you prefer to build incrementally, use these individual prompts:

### **Step 1: Data Conversion Script**
```
Create scripts/convert_csv_to_json.py that:
- Reads classification_results_awslabs.csv
- Converts each row to a JSON document with:
  - repository name
  - searchable_content (combined description + metadata)
  - metadata object with all fields
- Saves to data/repos/ directory (one file per repo)
- Includes error handling and progress logging
- Follow the format specified in design.md section 1.1
```

### **Step 2: CDK Infrastructure**
```
Create CDK TypeScript stack in cdk/ that:
- Defines S3 buckets for data, vectors, and frontend
- Creates Bedrock Knowledge Base with S3 Vectors configuration
- Sets up Data Source pointing to S3 bucket
- Creates Lambda function with proper IAM role
- Sets up API Gateway REST API with CORS
- Outputs KB ID, API URL, Frontend URL
- Follow exact configuration from design.md section 2
```

### **Step 3: Lambda Function**
```
Create lambda/lambda_function.py that:
- Imports Strands Agent and retrieve tool
- Uses system prompt from design.md section 3.1
- Implements conversation state management
- Handles POST requests from API Gateway
- Returns responses with proper CORS headers
- Includes error handling for Bedrock failures
- Follow exact implementation from design.md section 4.1
```

### **Step 4: Frontend**
```
Create web chatbot frontend with:
- index.html: Clean chat interface
- css/style.css: AWS-themed styling (orange/gray)
- js/api.js: API client with session management
- js/ui.js: UI manager for messages and loading states
- js/app.js: Main app logic connecting API and UI
- Follow exact design from design.md section 5.1
```

### **Step 5: Deployment Automation**
```
Create deployment automation:
- deploy.sh: Master deployment script
- scripts/sync_kb.sh: Knowledge Base sync script
- scripts/setup_monitoring.sh: CloudWatch setup
- Follow deployment.md phases 1-7
```

---

## **For Amazon Q Developer**

If using Amazon Q in your IDE:

```
@workspace I want to implement the AWS Solutions Architect Agent Chatbot.

Context:
- All documentation is in requirements.md, design.md, deployment.md
- Need to build: data scripts, CDK stack, Lambda function, frontend
- Tech: Bedrock, Strands Agents, S3 Vectors, Lambda, API Gateway

Start by creating scripts/convert_csv_to_json.py following the design 
in design.md section 1.1. The script should convert 
classification_results_awslabs.csv to JSON documents.
```

---

## **For GitHub Copilot**

Open files in this order and let Copilot suggest:

1. Create `scripts/convert_csv_to_json.py` - Add comment:
   ```python
   # Convert classification_results_awslabs.csv to JSON documents
   # for Bedrock Knowledge Base ingestion
   # Follow format from design.md section 1.1
   ```

2. Create `cdk/lib/cdk-stack.ts` - Add comment:
   ```typescript
   // AWS CDK stack for Solutions Architect Agent
   // Creates: S3 buckets, Bedrock KB, Lambda, API Gateway
   // Follow design.md section 2
   ```

3. Create `lambda/lambda_function.py` - Add comment:
   ```python
   # Lambda handler for Strands Agent
   # Handles chat requests and queries Bedrock KB
   # Follow design.md section 4.1
   ```

---

## **Manual Implementation**

If building manually, follow this order:

1. ✅ Read all documentation (requirements.md, design.md, deployment.md)
2. ✅ Set up AWS credentials and region (us-west-2)
3. ✅ Create data conversion script
4. ✅ Initialize CDK project
5. ✅ Create CDK stack
6. ✅ Create Lambda function
7. ✅ Create frontend
8. ✅ Follow deployment.md step-by-step

---

## **Verification Checklist**

After implementation, verify:

- [ ] Data conversion creates 925 JSON files
- [ ] CDK stack deploys without errors
- [ ] Knowledge Base sync completes successfully
- [ ] Lambda function responds to test requests
- [ ] API Gateway endpoint is accessible
- [ ] Frontend loads and displays chat interface
- [ ] Can send messages and receive responses
- [ ] Recommendations include GitHub URLs
- [ ] Costs are within budget ($50 alert set)

---

## **Getting Help**

If you encounter issues:

1. Check [deployment.md](deployment.md#troubleshooting) for common problems
2. Review CloudWatch logs for Lambda errors
3. Verify IAM permissions for all services
4. Check Bedrock model access is enabled
5. Ensure S3 Vectors preview is available in us-west-2

---

## **Quick Commands**

```bash
# Clone repo
git clone https://github.com/ajitnk-lab/awssa-chatbot.git
cd awssa-chatbot

# Convert data
python3 scripts/convert_csv_to_json.py

# Deploy infrastructure
cd cdk
cdk deploy

# Deploy Lambda
cd ../lambda
./deploy.sh

# Deploy frontend
cd ../frontend
aws s3 sync . s3://YOUR_FRONTEND_BUCKET/
```

---

**Ready to build? Start with the implementation prompt above!** 🚀
