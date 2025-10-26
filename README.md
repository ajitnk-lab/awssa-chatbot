# AWS Solutions Architect Agent Chatbot

An intelligent chatbot that helps customers find the right AWS sample projects from GitHub repositories based on their specific needs.

## Quick Access

### 🌐 Live Chatbots
**Custom RAG Agent**: https://d34pzvxmidb6ha.cloudfront.net  
**Q Business App**: https://6fvgkeyi.chat.qbusiness.us-east-1.on.aws?code=73e4f991-8b32-49d5-8fb3-8e03a3dcc5bc

### 📊 System Status
- **Knowledge Base**: 899 repositories indexed (97.2% success rate)
- **Vector Database**: OpenSearch Serverless (aws-repos-vectors)
- **Backend**: AWS Lambda with Bedrock Claude 3 Haiku
- **Q Business**: 60-day free trial (until Dec 25, 2025)
- **Status**: ✅ Production Ready

---

✅ **PRODUCTION READY** - Fully deployed with OpenSearch Serverless!

### Live URLs
- **Frontend**: https://d34pzvxmidb6ha.cloudfront.net
- **API**: https://yz7jfyr21c.execute-api.us-west-2.amazonaws.com/prod/chat

### What's Working
- ✅ Complete CDK infrastructure deployed
- ✅ Lambda function with Bedrock Claude 3 Haiku integration
- ✅ **OpenSearch Serverless vector database** with FAISS engine (collection: aws-repos-vectors)
- ✅ **Bedrock Knowledge Base** with OpenSearch integration (ID: TOJENJXGHW)
- ✅ **925 repositories successfully indexed** with proper Bedrock format
- ✅ API Gateway with CORS configuration
- ✅ Frontend chatbot interface deployed via CloudFront
- ✅ Cost-optimized for AWS Free Tier ($17-35/month)

### Features Demonstrated
- 🤖 Conversational AI with Solutions Architect expertise
- 🔍 Intelligent keyword-based routing to relevant recommendations
- 💬 Multi-turn conversations with context retention
- 📊 Specific GitHub URLs, setup times, and cost estimates
- 🌐 Production-ready web interface
- 💰 Detailed cost breakdowns and technical requirements

### Test the Chatbots

**Custom RAG Agent**: https://d34pzvxmidb6ha.cloudfront.net
- Uses structured CSV metadata with OpenSearch Serverless
- 925 awslabs repositories with custom classifications
- Business-oriented filtering (cost, setup time, competencies)

**Q Business App**: https://6fvgkeyi.chat.qbusiness.us-east-1.on.aws?code=73e4f991-8b32-49d5-8fb3-8e03a3dcc5bc
- Uses web crawler for fresh GitHub content
- Automatic content updates
- 60-day free trial (until Dec 25, 2025)

Try queries like:
- "I need a serverless API solution"
- "How do I process real-time IoT data?"
- "I want to build a machine learning model"
- "Show me quick-setup, low-cost compliance solutions"

## Architecture

This project implements an AI-powered Solutions Architect agent using:
- **Amazon Bedrock** (Claude 3 Haiku) for natural language understanding
- **OpenSearch Serverless** with FAISS engine for vector search
- **Bedrock Knowledge Base** with OpenSearch integration
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
            Bedrock (Claude + KB) → OpenSearch Serverless
```

## Documentation

- **[requirements.md](requirements.md)** - Complete requirements specification and business objectives
- **[design.md](design.md)** - Technical design, architecture, and implementation details
- **[deployment.md](deployment.md)** - Step-by-step deployment guide and infrastructure setup
- **[update-data.md](update-data.md)** - Guide for updating Knowledge Base with new CSV data

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
├── README.md                    # This file - project overview and quick start
├── requirements.md              # Business requirements and success criteria
├── design.md                    # Technical architecture and component design
├── deployment.md                # Infrastructure deployment guide
├── update-data.md               # Knowledge Base data update procedures
├── classification_results_awslabs.csv  # Repository metadata (925 repos)
├── convert_to_bedrock_format.py   # Bedrock format conversion script
├── create_opensearch_index.py    # OpenSearch index creation script
├── monitor_ingestion.py          # Ingestion monitoring utility
├── scripts/
│   ├── convert_csv_to_json.py   # Legacy data conversion script
│   ├── setup_monitoring.sh      # Monitoring setup automation
│   └── sync_kb.sh               # Knowledge Base sync utility
├── cdk/                         # CDK infrastructure code
│   ├── lib/
│   │   └── cdk-stack.ts        # Main stack definition with OpenSearch Serverless
│   └── package.json            # CDK dependencies
├── lambda/                      # Lambda function code
│   ├── lambda_function.py      # Main handler with Strands Agent
│   ├── deploy.sh               # Lambda deployment script
│   └── requirements.txt        # Python dependencies
└── frontend/                    # Web chatbot interface
    ├── index.html              # Main chatbot page
    ├── css/
    │   └── style.css           # Chatbot styling
    └── js/
        ├── app.js              # Main application logic
        ├── api.js              # API client for backend communication
        └── ui.js               # UI management and interactions
```

## Cost Estimate

### Custom RAG Agent
**One-Time Setup**
- Knowledge Base creation: $5-10
- Embeddings (925 repos): $5-10
- **Total**: $10-20

**Monthly (1000 queries)**
- OpenSearch Serverless: $1-2
- Lambda invocations: $0.20-1
- Bedrock LLM calls: $5-10
- API Gateway: $0.10-0.50
- S3 + CloudFront: $0.50-1
- **Total**: $7-15/month

**First Month Total**: $17-35

### Q Business App
**Current Status**: 60-day free trial (until Dec 25, 2025)

**After Free Trial**
- Consumption pricing: $200 for 30,000 units/month
- 2 units per query = 15,000 queries for $200/month
- Index charges: $0.140-0.264/hour for data crawling

**Comparison**: Custom RAG is more cost-effective for moderate usage

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
- **Vector DB**: OpenSearch Serverless (Bedrock Knowledge Base)
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
