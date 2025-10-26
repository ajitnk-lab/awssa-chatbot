# AWS Solutions Architect Agent Chatbot

An intelligent chatbot that helps customers find the right AWS sample projects from GitHub repositories based on their specific needs.

## Overview

This project implements an AI-powered Solutions Architect agent using:
- **Amazon Bedrock** (Claude 3 Haiku) for natural language understanding
- **Bedrock Knowledge Base** with S3 Vectors for semantic search
- **Strands Agents SDK** for agent orchestration
- **AWS Lambda** for serverless compute
- **API Gateway** for REST API
- **S3 + CloudFront** for web hosting

## Features

- 🤖 Conversational AI agent with Solutions Architect expertise
- 🔍 Semantic search across 925+ AWS sample repositories
- 💬 Multi-turn conversations with context retention
- 📊 Intelligent recommendations with explanations
- 🌐 Simple web chatbot interface
- 💰 Cost-optimized for AWS Free Tier ($17-35/month)

## Architecture

```
User Browser → CloudFront → S3 (Frontend)
                    ↓
            API Gateway → Lambda (Strands Agent)
                    ↓
            Bedrock (Claude + KB) → S3 Vectors
```

## Documentation

- **[requirements.md](requirements.md)** - Complete requirements specification
- **[design.md](design.md)** - Technical design and architecture
- **[deployment.md](deployment.md)** - Step-by-step deployment guide

## Quick Start

### Prerequisites

- AWS Account with Free Tier credits
- AWS CLI configured
- Node.js 18+ (for CDK)
- Python 3.12+
- Bedrock model access (Claude 3 Haiku, Titan Embeddings v2)

### Deployment

1. **Prepare Data**
   ```bash
   python3 scripts/convert_csv_to_json.py
   ```

2. **Deploy Infrastructure**
   ```bash
   cd cdk
   cdk deploy
   ```

3. **Sync Knowledge Base**
   ```bash
   aws bedrock-agent start-ingestion-job \
     --knowledge-base-id $KB_ID \
     --data-source-id $DS_ID
   ```

4. **Deploy Lambda**
   ```bash
   cd lambda
   ./deploy.sh
   ```

5. **Deploy Frontend**
   ```bash
   cd frontend
   aws s3 sync . s3://$FRONTEND_BUCKET/
   ```

See [deployment.md](deployment.md) for detailed instructions.

## Project Structure

```
.
├── README.md                    # This file
├── requirements.md              # Requirements specification
├── design.md                    # Technical design
├── deployment.md                # Deployment guide
├── classification_results_awslabs.csv  # Repository metadata
├── scripts/
│   └── convert_csv_to_json.py  # Data conversion script
├── cdk/                         # CDK infrastructure code
│   ├── lib/
│   │   └── cdk-stack.ts        # Main stack definition
│   └── package.json
├── lambda/                      # Lambda function code
│   ├── lambda_function.py      # Main handler
│   └── requirements.txt        # Python dependencies
└── frontend/                    # Web chatbot
    ├── index.html
    ├── css/
    │   └── style.css
    └── js/
        ├── app.js
        ├── api.js
        └── ui.js
```

## Cost Estimate

### One-Time Setup
- Knowledge Base creation: $5-10
- Embeddings (925 repos): $5-10
- **Total**: $10-20

### Monthly (1000 queries)
- S3 Vector storage: $1-2
- Lambda invocations: $0.20-1
- Bedrock LLM calls: $5-10
- API Gateway: $0.10-0.50
- S3 + CloudFront: $0.50-1
- **Total**: $7-15/month

**First Month Total**: $17-35

## Usage Examples

**Query 1**: "I need a serverless API solution"
```
Agent: I can help you with that! A few questions:
       1. What type of data will your API handle?
       2. What's your preferred programming language?
       
User: REST API with JSON, Python preferred

Agent: I recommend these solutions:
       1. aws-samples/serverless-api-gateway-lambda
          ✅ Perfect for REST APIs with Lambda
          ✅ Uses: API Gateway, Lambda, DynamoDB
          ✅ Language: Python
          ✅ Setup: < 1 hour
```

**Query 2**: "How do I process streaming IoT data?"
```
Agent: For streaming IoT data, I need to understand:
       1. How many devices?
       2. Data volume per second?
       
User: About 10,000 devices, 1KB per second each

Agent: I recommend:
       1. awslabs/amazon-kinesis-client-nodejs
          ✅ Handles 10K+ devices easily
          ✅ Uses: Kinesis, Lambda
          ✅ Real-time processing
```

## Technology Stack

- **Backend**: AWS Lambda (Python 3.12)
- **Agent Framework**: Strands Agents SDK
- **LLM**: Claude 3 Haiku (Amazon Bedrock)
- **Vector DB**: S3 Vectors (Bedrock Knowledge Base)
- **API**: Amazon API Gateway (REST)
- **Frontend**: HTML/CSS/JavaScript
- **Hosting**: S3 + CloudFront
- **IaC**: AWS CDK (TypeScript)

## Development

### Local Testing

Test Lambda function locally:
```bash
cd lambda
python3 -c "from lambda_function import lambda_handler; \
  print(lambda_handler({'body': '{\"message\": \"test\"}'}, None))"
```

### Monitoring

View Lambda logs:
```bash
aws logs tail /aws/lambda/AwsReposAgentStack-AgentFunction --follow
```

Check costs:
```bash
aws ce get-cost-and-usage \
  --time-period Start=2025-10-01,End=2025-10-31 \
  --granularity DAILY \
  --metrics BlendedCost
```

## Troubleshooting

See [deployment.md](deployment.md#troubleshooting) for common issues and solutions.

## Contributing

This is a proof-of-concept project. Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Built with [Strands Agents SDK](https://strandsagents.com/)
- Uses AWS sample repositories from [aws-samples](https://github.com/aws-samples) and [awslabs](https://github.com/awslabs)
- Powered by Amazon Bedrock and Claude 3

## Contact

For questions or feedback, please open an issue.

---

**Status**: Ready for Deployment  
**Version**: 1.0  
**Last Updated**: 2025-10-26
