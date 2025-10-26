# AWS Solutions Architect Agent - Requirements Document

## Project Overview

Build an intelligent AWS Solutions Architect chatbot that helps customers find the right AWS sample projects from GitHub repositories based on their specific needs and requirements.

---

## Business Objectives

### Primary Goal
Enable customers to discover relevant AWS sample projects through natural language conversation, reducing time-to-solution from hours to minutes.

### Success Metrics
- **Time to Solution**: < 10 minutes per query (vs 30-60 minutes manual search)
- **Recommendation Accuracy**: 70-80% relevance
- **User Satisfaction**: Positive feedback on recommendations
- **Cost Efficiency**: Stay within AWS Free Tier budget ($100-200 credits)

---

## Functional Requirements

### FR-1: Conversational Interface
**Priority**: CRITICAL

The agent must:
- Accept natural language queries from users
- Ask clarifying questions to understand requirements
- Maintain conversation context across multiple turns
- Provide responses in clear, professional language

**Example Interaction**:
```
User: "I need to build a serverless API"
Agent: "I can help you with that! A few questions:
        1. What type of data will your API handle?
        2. Do you need real-time or batch processing?
        3. What's your preferred programming language?"
```

---

### FR-2: Intelligent Repository Search
**Priority**: CRITICAL

The agent must:
- Query Bedrock Knowledge Base with semantic search
- Match customer requirements to repository metadata
- Filter by multiple criteria (AWS services, language, complexity)
- Rank results by relevance

**Search Criteria**:
- Technical competencies (ML, Security, Modern App Dev, etc.)
- AWS services used
- Programming language
- Solution type (Foundation Builders, Innovation Catalysts, etc.)
- Customer problems addressed
- Setup time and cost range

---

### FR-3: Contextual Recommendations
**Priority**: CRITICAL

The agent must:
- Recommend 2-3 most relevant repositories
- Explain WHY each recommendation fits the use case
- Highlight key features and benefits
- Provide trade-offs between options

**Recommendation Format**:
```
"I recommend these solutions:

1. aws-samples/serverless-api-gateway-lambda
   ✅ Perfect for: REST API with Lambda backend
   ✅ Uses: API Gateway, Lambda, DynamoDB
   ✅ Language: Python
   ✅ Setup: < 1 hour
   ⚠️  Note: Requires basic Lambda knowledge

2. aws-samples/apigw-lambda-dynamodb
   ✅ Perfect for: Simple CRUD operations
   ✅ Uses: API Gateway, Lambda, DynamoDB
   ✅ Language: Node.js
   ✅ Setup: < 30 minutes
   
Which approach interests you more?"
```

---

### FR-4: Multi-Turn Conversation
**Priority**: HIGH

The agent must:
- Remember previous questions and answers
- Refine recommendations based on follow-up questions
- Handle clarifications and corrections
- Allow users to explore alternatives

**Example Flow**:
```
User: "I need a data pipeline"
Agent: "What type of data? Batch or streaming?"
User: "Streaming from IoT devices"
Agent: "How many devices?"
User: "About 10,000"
Agent: [Recommends Kinesis-based solutions]
User: "What about cost?"
Agent: [Provides cost estimates for recommended solutions]
```

---

### FR-5: Web Chatbot Interface
**Priority**: HIGH

The chatbot must:
- Provide clean, modern web interface
- Display conversation history
- Show repository links and metadata
- Support markdown formatting in responses
- Be mobile-responsive

**UI Components**:
- Chat message area (scrollable)
- Input text box
- Send button
- Repository cards with links
- Loading indicators

---

## Non-Functional Requirements

### NFR-1: Performance
**Priority**: HIGH

- **Response Time**: < 5 seconds for simple queries
- **Response Time**: < 10 seconds for complex queries with KB search
- **Concurrent Users**: Support 10+ simultaneous users
- **Availability**: 99% uptime during business hours

---

### NFR-2: Cost Constraints
**Priority**: CRITICAL

**Budget**: $100-200 AWS Free Tier credits

**Cost Breakdown**:
- Bedrock KB creation: $5-10 (one-time)
- Embeddings (925 repos): $5-10 (one-time)
- S3 Vector storage: $1-2/month
- Lambda invocations: $0.20-1/month (1000 queries)
- Bedrock LLM calls: $5-10/month (1000 queries with Haiku)
- API Gateway: $0.10-0.50/month
- S3 + CloudFront: $0.50-1/month

**Total Estimated**: $15-30 for setup + $7-15/month

**Cost Optimization**:
- Use Claude 3 Haiku (cheapest model)
- Use S3 Vectors (90% cheaper than OpenSearch)
- Lambda (pay-per-use, no idle costs)
- Set billing alerts at $50

---

### NFR-3: Security
**Priority**: HIGH

- **Authentication**: Public access (no auth for MVP)
- **Data Privacy**: No PII storage
- **API Security**: API Gateway throttling (100 req/min)
- **IAM**: Least privilege for Lambda execution role
- **Encryption**: S3 buckets encrypted at rest

---

### NFR-4: Scalability
**Priority**: MEDIUM

- **Lambda**: Auto-scales to handle traffic
- **Knowledge Base**: Supports 925 repos (can scale to 10K+)
- **S3 Vectors**: Unlimited storage capacity
- **API Gateway**: Handles 10K requests/second

---

### NFR-5: Maintainability
**Priority**: MEDIUM

- **Infrastructure as Code**: All resources defined in CDK
- **Observability**: CloudWatch logs for Lambda
- **Monitoring**: CloudWatch metrics for API Gateway
- **Versioning**: Git for code, S3 versioning for data

---

## Technical Requirements

### TR-1: Data Source
**Priority**: CRITICAL

**Input**: `classification_results_awslabs.csv`
- 925 AWS Labs repositories
- Metadata: description, AWS services, languages, etc.

**Processing**:
- Convert CSV to JSON documents
- Enrich with searchable content
- Upload to S3 bucket

---

### TR-2: Knowledge Base
**Priority**: CRITICAL

**Technology**: Amazon Bedrock Knowledge Base with S3 Vectors

**Configuration**:
- **Vector Store**: S3 Vectors (preview)
- **Embedding Model**: Amazon Titan Text Embeddings v2
- **Data Source**: S3 bucket with JSON documents
- **Sync**: Manual sync after data upload

**Document Format**:
```json
{
  "repository": "awslabs/aws-security-automation",
  "searchable_content": "Collection of scripts and resources for DevSecOps and Automated Incident Response Security. Solution Type: Compliance Accelerators. Technical Competency: Security, Compliance. Customer Problems: Security Gaps, Compliance Burden, Audit Failures. AWS Services: General AWS. Primary Language: Python.",
  "metadata": {
    "url": "https://github.com/awslabs/aws-security-automation",
    "solution_type": "Compliance Accelerators",
    "technical_competencies": "Security, Compliance",
    "aws_services": "General AWS",
    "customer_problems": "Security Gaps, Compliance Burden, Audit Failures",
    "primary_language": "Python",
    "setup_time": "Quick Setup (< 1 hour)",
    "cost_range": "Low ($10-100/month)",
    "stars": 150,
    "genai_agentic": "No"
  }
}
```

---

### TR-3: Strands Agent
**Priority**: CRITICAL

**Technology**: Strands Agents SDK

**Configuration**:
- **Model**: Claude 3 Haiku (us-west-2)
- **Tools**: `retrieve` (Bedrock KB query)
- **System Prompt**: Solutions Architect persona
- **Deployment**: AWS Lambda (Python 3.12)

**Agent Capabilities**:
- Natural language understanding
- Multi-turn conversation
- Knowledge base querying
- Contextual recommendations

---

### TR-4: API Layer
**Priority**: CRITICAL

**Technology**: Amazon API Gateway (REST API)

**Endpoints**:
- `POST /chat` - Send message to agent
  - Request: `{"message": "I need a serverless API", "session_id": "uuid"}`
  - Response: `{"response": "...", "session_id": "uuid"}`

**Configuration**:
- CORS enabled for web frontend
- Throttling: 100 requests/minute
- Timeout: 30 seconds

---

### TR-5: Web Frontend
**Priority**: HIGH

**Technology**: Static HTML/CSS/JavaScript

**Hosting**: S3 + CloudFront

**Features**:
- Simple chat interface
- Message history
- Repository cards with links
- Loading indicators
- Error handling

**Libraries**:
- No framework (vanilla JS)
- Markdown rendering (marked.js)
- Syntax highlighting (highlight.js)

---

## Data Requirements

### DR-1: Repository Metadata
**Priority**: CRITICAL

**Source**: `classification_results_awslabs.csv` (925 repos)

**Required Fields**:
- repository (name)
- url
- description
- solution_type
- technical_competencies
- aws_services
- customer_problems
- primary_language
- setup_time
- cost_range
- genai_agentic

**Data Quality**:
- 73% have descriptions
- 100% have classification fields
- 41.5% have sufficient data for recommendations

---

### DR-2: Conversation State
**Priority**: HIGH

**Storage**: In-memory (Lambda execution context)

**Data**:
- Session ID
- Conversation history (last 10 messages)
- User preferences extracted from conversation

**Retention**: Session duration only (no persistence)

---

## Constraints

### C-1: AWS Region
**Constraint**: us-west-2 (Oregon)

**Reason**: Best Bedrock model availability

---

### C-2: Free Tier Account
**Constraint**: Must stay within $100-200 credit budget

**Implications**:
- Use cheapest models (Haiku)
- Use S3 Vectors (not OpenSearch)
- Minimize API calls
- Set billing alerts

---

### C-3: Data Quality
**Constraint**: Current CSV has limited metadata

**Implications**:
- Agent effectiveness: 60-70% (not 80-90%)
- Some recommendations may be generic
- Will improve when metadata is enriched

---

### C-4: Preview Features
**Constraint**: S3 Vectors is in preview

**Implications**:
- May have bugs or limitations
- API may change
- Not recommended for production (OK for POC)

---

## Out of Scope

### OS-1: Authentication
- No user login/signup
- No user profiles
- Public access only

### OS-2: Conversation Persistence
- No conversation history storage
- No session recovery after timeout
- Stateless between sessions

### OS-3: Advanced Features
- No multi-language support
- No voice interface
- No mobile app
- No analytics dashboard

### OS-4: Data Enrichment
- No automatic README fetching
- No GitHub API integration
- No real-time repo updates
- Metadata enrichment is separate project

---

## Acceptance Criteria

### AC-1: Functional
- ✅ User can ask questions in natural language
- ✅ Agent asks clarifying questions
- ✅ Agent recommends 2-3 relevant repositories
- ✅ Agent explains why each repo fits
- ✅ User can click links to GitHub repos
- ✅ Conversation maintains context

### AC-2: Performance
- ✅ Response time < 10 seconds
- ✅ Handles 10 concurrent users
- ✅ No crashes or errors

### AC-3: Cost
- ✅ Total cost < $50 for setup + 1 month
- ✅ Billing alerts configured
- ✅ No unexpected charges

### AC-4: Quality
- ✅ Recommendations are relevant (60-70% accuracy)
- ✅ Explanations are clear and helpful
- ✅ UI is clean and functional

---

## Risks and Mitigations

### Risk 1: S3 Vectors Preview Issues
**Probability**: Medium  
**Impact**: High  
**Mitigation**: Have OpenSearch Serverless as backup plan

### Risk 2: Credit Exhaustion
**Probability**: Medium  
**Impact**: High  
**Mitigation**: Set $50 billing alert, use Haiku model, monitor costs daily

### Risk 3: Poor Recommendation Quality
**Probability**: High  
**Impact**: Medium  
**Mitigation**: Set expectations, improve metadata in parallel, iterate on prompts

### Risk 4: Lambda Cold Starts
**Probability**: Medium  
**Impact**: Low  
**Mitigation**: Accept 2-5 second cold starts, or use provisioned concurrency if needed

---

## Dependencies

### External Dependencies
- AWS Account with Free Tier credits
- Bedrock model access (Claude 3 Haiku, Titan Embeddings v2)
- S3 Vectors preview access (us-west-2)
- GitHub repository data (CSV file)

### Internal Dependencies
- Metadata enrichment project (separate, in progress)
- CSV data quality improvements (future)

---

## Timeline

### Phase 1: Infrastructure Setup (Day 1)
- Convert CSV to JSON
- Upload to S3
- Create Bedrock Knowledge Base with S3 Vectors
- Sync data source

### Phase 2: Agent Development (Day 2)
- Install Strands SDK
- Create agent with system prompt
- Implement KB query tool
- Test locally

### Phase 3: API & Deployment (Day 3)
- Create Lambda function
- Deploy Strands agent to Lambda
- Create API Gateway
- Test API endpoints

### Phase 4: Web Frontend (Day 4)
- Build HTML/CSS/JS chatbot
- Integrate with API
- Deploy to S3 + CloudFront
- Test end-to-end

### Phase 5: Testing & Refinement (Day 5)
- Test with real scenarios
- Refine prompts
- Monitor costs
- Document usage

**Total Estimated Time**: 5 days

---

## Appendix

### A1: Sample Queries
- "I need to build a serverless API"
- "How do I process streaming data from IoT devices?"
- "I want to implement ML model deployment"
- "I need a security automation solution"
- "How do I build a data pipeline?"

### A2: Sample Repositories
- awslabs/aws-security-automation
- awslabs/serverless-image-handler
- awslabs/amazon-kinesis-client-nodejs
- awslabs/aws-deployment-framework

### A3: Technology Stack
- **Backend**: AWS Lambda (Python 3.12)
- **Agent Framework**: Strands Agents SDK
- **LLM**: Claude 3 Haiku (Bedrock)
- **Vector DB**: S3 Vectors (Bedrock KB)
- **API**: API Gateway (REST)
- **Frontend**: HTML/CSS/JavaScript
- **Hosting**: S3 + CloudFront
- **IaC**: AWS CDK (TypeScript)

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-26  
**Status**: Approved for Implementation
