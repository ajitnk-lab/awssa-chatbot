# AWS Solutions Architect Agent - Design Document

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Web Chatbot (HTML/CSS/JS)                    │  │
│  │  - Chat interface                                         │  │
│  │  - Message history                                        │  │
│  │  - Repository cards                                       │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CloudFront Distribution                       │
│  - CDN for static content                                       │
│  - HTTPS termination                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      S3 Bucket (Frontend)                        │
│  - Static website hosting                                       │
│  - HTML, CSS, JS files                                          │
└─────────────────────────────────────────────────────────────────┘

                             │ POST /chat
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway (REST API)                        │
│  - CORS enabled                                                 │
│  - Throttling: 100 req/min                                      │
│  - Timeout: 30 seconds                                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Lambda Function (Python 3.12)                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Strands Agent                                │  │
│  │  - System Prompt: Solutions Architect                    │  │
│  │  - Model: Claude 3 Haiku                                 │  │
│  │  - Tools: retrieve (KB query)                            │  │
│  │  - Conversation state management                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Memory: 1024 MB                                                │
│  Timeout: 30 seconds                                            │
│  Runtime: Python 3.12                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Amazon Bedrock (us-west-2)                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Claude 3 Haiku                                           │  │
│  │  - Model ID: anthropic.claude-3-haiku-20240307-v1:0      │  │
│  │  - Max tokens: 4096                                       │  │
│  │  - Temperature: 0.7                                       │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Knowledge Base                                           │  │
│  │  - KB ID: XXXXXXXXXX                                      │  │
│  │  - Embedding: Titan Text v2                              │  │
│  │  - Vector Store: S3 Vectors                              │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    S3 Vectors (Vector Store)                     │
│  - 925 repository embeddings                                    │
│  - Titan Text Embeddings v2 (1024 dimensions)                  │
│  - Sub-second query latency                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  S3 Bucket (Data Source)                         │
│  - JSON documents (925 repos)                                   │
│  - Metadata + searchable content                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Data Processing Layer

#### 1.1 CSV to JSON Converter

**Purpose**: Transform CSV data into KB-friendly JSON documents

**Input**: `classification_results_awslabs.csv`

**Output**: JSON files in S3

**Processing Logic**:
```python
def convert_csv_to_json(csv_file):
    """
    Convert CSV to enriched JSON documents for KB ingestion
    """
    repos = []
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Create searchable content by combining key fields
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
            """
            
            # Create structured document
            doc = {
                "repository": row['repository'],
                "url": row['url'],
                "searchable_content": searchable_content.strip(),
                "metadata": {
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
            
            repos.append(doc)
    
    return repos
```

**File Structure**:
```
s3://kb-data-bucket/
  ├── repos/
  │   ├── awslabs-amazon-kinesis-client-nodejs.json
  │   ├── awslabs-aws-security-automation.json
  │   └── ... (925 files)
```

---

### 2. Knowledge Base Layer

#### 2.1 Bedrock Knowledge Base Configuration

**Vector Store**: S3 Vectors (Preview)

**Embedding Model**: Amazon Titan Text Embeddings v2
- Model ARN: `arn:aws:bedrock:us-west-2::foundation-model/amazon.titan-embed-text-v2:0`
- Dimensions: 1024
- Normalize: true

**Data Source**: S3 bucket with JSON documents

**Chunking Strategy**:
- Strategy: Default (semantic)
- Max tokens: 300
- Overlap: 20%

**Metadata Filtering**: Enabled
- Filter by: solution_type, technical_competencies, aws_services, primary_language

**CDK Configuration**:
```typescript
const knowledgeBase = new bedrock.CfnKnowledgeBase(this, 'RepoKB', {
  name: 'aws-repos-knowledge-base',
  roleArn: kbRole.roleArn,
  knowledgeBaseConfiguration: {
    type: 'VECTOR',
    vectorKnowledgeBaseConfiguration: {
      embeddingModelArn: 'arn:aws:bedrock:us-west-2::foundation-model/amazon.titan-embed-text-v2:0',
      embeddingModelConfiguration: {
        bedrockEmbeddingModelConfiguration: {
          dimensions: 1024
        }
      }
    }
  },
  storageConfiguration: {
    type: 'S3_VECTORS',
    s3VectorsConfiguration: {
      vectorBucketArn: vectorBucket.bucketArn
    }
  }
});
```

---

### 3. Agent Layer

#### 3.1 Strands Agent Design

**System Prompt**:
```python
SYSTEM_PROMPT = """
You are an expert AWS Solutions Architect helping customers find the right 
AWS sample projects from GitHub for their specific needs.

Your approach:
1. UNDERSTAND: Ask 2-3 clarifying questions to understand:
   - Their specific problem or use case
   - Technical requirements (AWS services, programming language)
   - Constraints (budget, timeline, team expertise)
   - Scale requirements (POC vs production)

2. SEARCH: Use the retrieve tool to query the knowledge base with:
   - Key terms from customer's description
   - Relevant AWS services
   - Technical competencies needed

3. RECOMMEND: Provide 2-3 most relevant repositories with:
   - Repository name and GitHub URL
   - Why it fits their use case (specific reasons)
   - Key features and AWS services used
   - Setup time and cost estimate
   - Prerequisites and complexity level
   - Trade-offs compared to alternatives

4. REFINE: Ask if they need more details or alternative solutions

Guidelines:
- Be conversational and helpful, not robotic
- Explain technical concepts clearly
- Prioritize solutions that match their constraints
- If no perfect match, recommend closest alternatives
- Always provide GitHub URLs for recommended repos
- Keep responses concise but informative

Remember: You're helping them save time by finding the right solution quickly.
"""
```

**Agent Configuration**:
```python
from strands import Agent
from strands_tools import retrieve

agent = Agent(
    system_prompt=SYSTEM_PROMPT,
    tools=[retrieve],
    model_provider='bedrock',
    model_config={
        'model_id': 'anthropic.claude-3-haiku-20240307-v1:0',
        'region': 'us-west-2',
        'max_tokens': 4096,
        'temperature': 0.7
    },
    tool_config={
        'retrieve': {
            'knowledge_base_id': 'XXXXXXXXXX',  # From CDK output
            'max_results': 10,
            'min_score': 0.5
        }
    }
)
```

**Conversation State Management**:
```python
class ConversationManager:
    def __init__(self):
        self.sessions = {}  # session_id -> conversation_history
    
    def get_or_create_session(self, session_id):
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'history': [],
                'context': {},
                'created_at': time.time()
            }
        return self.sessions[session_id]
    
    def add_message(self, session_id, role, content):
        session = self.get_or_create_session(session_id)
        session['history'].append({
            'role': role,
            'content': content,
            'timestamp': time.time()
        })
        
        # Keep only last 10 messages
        if len(session['history']) > 10:
            session['history'] = session['history'][-10:]
    
    def get_history(self, session_id):
        session = self.get_or_create_session(session_id)
        return session['history']
```

---

### 4. API Layer

#### 4.1 Lambda Function Handler

**Function Structure**:
```python
# lambda_function.py

import json
import os
from strands import Agent
from strands_tools import retrieve

# Initialize agent (outside handler for reuse)
agent = Agent(
    system_prompt=SYSTEM_PROMPT,
    tools=[retrieve],
    model_provider='bedrock',
    model_config={
        'model_id': 'anthropic.claude-3-haiku-20240307-v1:0',
        'region': 'us-west-2',
        'max_tokens': 4096
    },
    tool_config={
        'retrieve': {
            'knowledge_base_id': os.environ['KB_ID'],
            'max_results': 10
        }
    }
)

# Conversation manager (in-memory)
conversation_manager = ConversationManager()

def lambda_handler(event, context):
    """
    Handle chat requests from API Gateway
    """
    try:
        # Parse request
        body = json.loads(event['body'])
        message = body['message']
        session_id = body.get('session_id', str(uuid.uuid4()))
        
        # Get conversation history
        history = conversation_manager.get_history(session_id)
        
        # Add user message to history
        conversation_manager.add_message(session_id, 'user', message)
        
        # Build context for agent
        context = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in history[-5:]  # Last 5 messages
        ])
        
        # Query agent
        prompt = f"{context}\nuser: {message}" if context else message
        response = agent(prompt)
        
        # Add agent response to history
        conversation_manager.add_message(session_id, 'assistant', response)
        
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

**Lambda Configuration**:
- Runtime: Python 3.12
- Memory: 1024 MB
- Timeout: 30 seconds
- Environment Variables:
  - `KB_ID`: Bedrock Knowledge Base ID
  - `AWS_REGION`: us-west-2

**IAM Role Permissions**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:Retrieve"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

---

#### 4.2 API Gateway Configuration

**API Type**: REST API

**Endpoints**:

**POST /chat**
- Integration: Lambda Proxy
- CORS: Enabled
- Throttling: 100 requests/minute
- Timeout: 30 seconds

**Request Schema**:
```json
{
  "message": "string (required)",
  "session_id": "string (optional, UUID)"
}
```

**Response Schema**:
```json
{
  "response": "string",
  "session_id": "string"
}
```

**CORS Configuration**:
```typescript
api.addCorsPreflight('/chat', {
  allowOrigins: ['*'],
  allowMethods: ['POST', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization']
});
```

---

### 5. Frontend Layer

#### 5.1 Web Chatbot Design

**Technology**: Vanilla HTML/CSS/JavaScript

**File Structure**:
```
frontend/
├── index.html
├── css/
│   └── style.css
├── js/
│   ├── app.js
│   ├── api.js
│   └── ui.js
└── assets/
    └── logo.png
```

**Key Components**:

**HTML Structure** (`index.html`):
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWS Solutions Architect Agent</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>AWS Solutions Architect Agent</h1>
            <p>Find the right AWS sample project for your needs</p>
        </header>
        
        <div id="chat-container">
            <div id="messages"></div>
        </div>
        
        <div id="input-container">
            <textarea id="user-input" placeholder="Describe what you're trying to build..."></textarea>
            <button id="send-btn">Send</button>
        </div>
        
        <div id="loading" class="hidden">
            <span>Agent is thinking...</span>
        </div>
    </div>
    
    <script src="js/api.js"></script>
    <script src="js/ui.js"></script>
    <script src="js/app.js"></script>
</body>
</html>
```

**API Client** (`js/api.js`):
```javascript
class ChatAPI {
    constructor(apiUrl) {
        this.apiUrl = apiUrl;
        this.sessionId = this.getOrCreateSessionId();
    }
    
    getOrCreateSessionId() {
        let sessionId = localStorage.getItem('session_id');
        if (!sessionId) {
            sessionId = this.generateUUID();
            localStorage.setItem('session_id', sessionId);
        }
        return sessionId;
    }
    
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    async sendMessage(message) {
        const response = await fetch(`${this.apiUrl}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: this.sessionId
            })
        });
        
        if (!response.ok) {
            throw new Error('API request failed');
        }
        
        return await response.json();
    }
}
```

**UI Manager** (`js/ui.js`):
```javascript
class ChatUI {
    constructor() {
        this.messagesContainer = document.getElementById('messages');
        this.userInput = document.getElementById('user-input');
        this.sendBtn = document.getElementById('send-btn');
        this.loading = document.getElementById('loading');
    }
    
    addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = this.formatContent(content);
        
        messageDiv.appendChild(contentDiv);
        this.messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    formatContent(content) {
        // Convert markdown-style links to HTML
        content = content.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
        
        // Convert line breaks
        content = content.replace(/\n/g, '<br>');
        
        return content;
    }
    
    showLoading() {
        this.loading.classList.remove('hidden');
        this.sendBtn.disabled = true;
    }
    
    hideLoading() {
        this.loading.classList.add('hidden');
        this.sendBtn.disabled = false;
    }
    
    clearInput() {
        this.userInput.value = '';
    }
}
```

**Main App** (`js/app.js`):
```javascript
const API_URL = 'https://YOUR_API_GATEWAY_URL';

const api = new ChatAPI(API_URL);
const ui = new ChatUI();

// Send message on button click
ui.sendBtn.addEventListener('click', async () => {
    const message = ui.userInput.value.trim();
    if (!message) return;
    
    // Add user message to UI
    ui.addMessage('user', message);
    ui.clearInput();
    ui.showLoading();
    
    try {
        // Send to API
        const response = await api.sendMessage(message);
        
        // Add agent response to UI
        ui.addMessage('assistant', response.response);
    } catch (error) {
        ui.addMessage('error', 'Sorry, something went wrong. Please try again.');
        console.error(error);
    } finally {
        ui.hideLoading();
    }
});

// Send message on Enter key
ui.userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        ui.sendBtn.click();
    }
});

// Initial greeting
ui.addMessage('assistant', 'Hi! I\'m your AWS Solutions Architect. What are you trying to build?');
```

**Styling** (`css/style.css`):
```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: #f5f5f5;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    height: 100vh;
    display: flex;
    flex-direction: column;
}

header {
    text-align: center;
    margin-bottom: 20px;
}

header h1 {
    color: #232f3e;
    font-size: 24px;
}

header p {
    color: #666;
    font-size: 14px;
}

#chat-container {
    flex: 1;
    background: white;
    border-radius: 8px;
    padding: 20px;
    overflow-y: auto;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.message {
    margin-bottom: 15px;
    display: flex;
}

.message.user {
    justify-content: flex-end;
}

.message.assistant {
    justify-content: flex-start;
}

.message-content {
    max-width: 70%;
    padding: 12px 16px;
    border-radius: 8px;
    line-height: 1.5;
}

.message.user .message-content {
    background: #ff9900;
    color: white;
}

.message.assistant .message-content {
    background: #f0f0f0;
    color: #232f3e;
}

.message.error .message-content {
    background: #ffebee;
    color: #c62828;
}

#input-container {
    display: flex;
    gap: 10px;
}

#user-input {
    flex: 1;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 14px;
    resize: none;
    height: 60px;
}

#send-btn {
    padding: 12px 24px;
    background: #ff9900;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: bold;
}

#send-btn:hover {
    background: #ec7211;
}

#send-btn:disabled {
    background: #ccc;
    cursor: not-allowed;
}

#loading {
    text-align: center;
    color: #666;
    font-size: 14px;
    margin-top: 10px;
}

.hidden {
    display: none;
}

a {
    color: #0073bb;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}
```

---

## Data Flow

### Request Flow

```
1. User types message in web chatbot
   ↓
2. JavaScript sends POST to API Gateway
   {
     "message": "I need a serverless API",
     "session_id": "uuid"
   }
   ↓
3. API Gateway invokes Lambda function
   ↓
4. Lambda handler:
   a. Retrieves conversation history
   b. Adds user message to history
   c. Calls Strands agent with context
   ↓
5. Strands agent:
   a. Processes message with LLM (Claude Haiku)
   b. Decides to query KB or respond directly
   c. If KB query needed:
      - Calls retrieve tool
      - Bedrock KB searches S3 Vectors
      - Returns top 10 results
   d. LLM generates response with recommendations
   ↓
6. Lambda returns response to API Gateway
   {
     "response": "I recommend...",
     "session_id": "uuid"
   }
   ↓
7. API Gateway returns to web chatbot
   ↓
8. JavaScript displays response in chat UI
```

---

## Security Design

### Authentication & Authorization
- **Frontend**: Public access (no auth)
- **API Gateway**: No authentication (MVP)
- **Lambda**: IAM role with least privilege
- **Bedrock**: IAM permissions for Lambda role

### Data Security
- **In Transit**: HTTPS/TLS 1.2+
- **At Rest**: S3 encryption (SSE-S3)
- **Secrets**: No secrets stored (uses IAM roles)

### Rate Limiting
- **API Gateway**: 100 requests/minute per IP
- **Lambda**: Concurrent execution limit: 10

### CORS Policy
```javascript
{
  "allowOrigins": ["*"],  // Restrict to specific domain in production
  "allowMethods": ["POST", "OPTIONS"],
  "allowHeaders": ["Content-Type"]
}
```

---

## Monitoring & Observability

### CloudWatch Logs
- **Lambda**: All invocations logged
- **Log Retention**: 7 days
- **Log Groups**:
  - `/aws/lambda/solutions-architect-agent`

### CloudWatch Metrics
- **Lambda**:
  - Invocations
  - Duration
  - Errors
  - Throttles
- **API Gateway**:
  - Request count
  - Latency
  - 4XX/5XX errors

### Alarms
- **Lambda Errors**: > 5 errors in 5 minutes
- **API Gateway 5XX**: > 10 errors in 5 minutes
- **Lambda Duration**: > 25 seconds (approaching timeout)

### Cost Monitoring
- **Billing Alert**: $50 threshold
- **Daily Cost Check**: Manual review
- **Budget**: $100/month

---

## Error Handling

### Lambda Error Handling
```python
try:
    # Process request
    response = agent(prompt)
    return success_response(response)
except BedrockException as e:
    logger.error(f"Bedrock error: {e}")
    return error_response("AI service unavailable", 503)
except TimeoutError as e:
    logger.error(f"Timeout: {e}")
    return error_response("Request timeout", 504)
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return error_response("Internal error", 500)
```

### Frontend Error Handling
```javascript
try {
    const response = await api.sendMessage(message);
    ui.addMessage('assistant', response.response);
} catch (error) {
    if (error.status === 503) {
        ui.addMessage('error', 'AI service is temporarily unavailable. Please try again.');
    } else if (error.status === 504) {
        ui.addMessage('error', 'Request timed out. Please try a simpler query.');
    } else {
        ui.addMessage('error', 'Something went wrong. Please try again.');
    }
}
```

---

## Performance Optimization

### Lambda Optimization
- **Memory**: 1024 MB (balance cost vs performance)
- **Provisioned Concurrency**: None (accept cold starts)
- **Code Size**: Use Lambda Layers for Strands SDK
- **Connection Reuse**: Initialize agent outside handler

### Knowledge Base Optimization
- **Chunking**: 300 tokens (optimal for semantic search)
- **Max Results**: 10 (balance relevance vs latency)
- **Min Score**: 0.5 (filter low-quality matches)

### Frontend Optimization
- **CDN**: CloudFront for static assets
- **Caching**: Browser cache for CSS/JS (1 day)
- **Compression**: Gzip enabled
- **Lazy Loading**: Load chat history on demand

---

## Scalability Considerations

### Current Limits
- **Lambda**: 10 concurrent executions
- **API Gateway**: 100 requests/minute
- **Knowledge Base**: 925 repos (can scale to 10K+)

### Scaling Strategy
- **Horizontal**: Lambda auto-scales
- **Vertical**: Increase Lambda memory if needed
- **Data**: Add more repos without code changes
- **Users**: Can handle 100+ concurrent users

---

## Testing Strategy

### Unit Tests
- Lambda handler logic
- Conversation state management
- Error handling

### Integration Tests
- API Gateway → Lambda
- Lambda → Bedrock
- End-to-end flow

### Manual Tests
- Test queries (see requirements.md)
- Edge cases (empty input, long messages)
- Error scenarios (timeout, service unavailable)

---

## Deployment Strategy

See `deployment.md` for detailed deployment instructions.

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-26  
**Status**: Ready for Implementation
