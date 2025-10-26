# Updating Knowledge Base Data

This guide explains how to update the OpenSearch Serverless Knowledge Base with new repository data from CSV files.

## Overview

The system uses a specific Bedrock format for documents that requires conversion from CSV. This process ensures compatibility with OpenSearch Serverless and prevents object mapping errors.

## Prerequisites

- AWS CLI configured with proper permissions
- Python 3.12+ installed
- Access to the existing Knowledge Base (ID: TOJENJXGHW)
- New CSV file with repository data

## Process

### Step 1: Prepare New CSV File

Replace the existing CSV file with your new data:

```bash
# Backup existing file (optional)
cp classification_results_awslabs.csv classification_results_awslabs.csv.backup

# Copy new CSV file
cp /path/to/new_file.csv classification_results_awslabs.csv
```

**Required CSV Columns**:
- `repository` - Repository name (e.g., "awslabs/aws-security-automation")
- `url` - GitHub URL
- `description` - Repository description
- `solution_type` - Solution category
- `technical_competencies` - Technical skills required
- `aws_services` - AWS services used
- `customer_problems` - Problems it solves
- `primary_language` - Programming language
- `setup_time` - Time to setup
- `cost_range` - Cost estimate
- `genai_agentic` - GenAI/Agentic flag
- `stars` - GitHub stars (optional)

### Step 2: Convert to Bedrock Format

Run the conversion script:

```bash
python3 convert_to_bedrock_format.py
```

This script:
- Reads the CSV file
- Converts each row to Bedrock format with "text" and "metadata" fields
- Saves JSON files to `repos_bedrock/` directory
- Handles proper formatting to prevent object mapping errors

**Output**: JSON files in `repos_bedrock/` directory with format:
```json
{
  "text": "Repository description and searchable content...",
  "metadata": {
    "repository": "awslabs/example-repo",
    "url": "https://github.com/awslabs/example-repo",
    "solution_type": "Foundation Builders",
    "technical_competencies": "Modern App Dev",
    "aws_services": "Lambda, API Gateway",
    "customer_problems": "API Development",
    "primary_language": "Python",
    "setup_time": "Quick Setup (< 1 hour)",
    "cost_range": "Low ($10-100/month)",
    "stars": 150,
    "genai_agentic": "No"
  }
}
```

### Step 3: Upload to S3

Upload the converted files to the S3 data source:

```bash
# Upload to S3 bucket
aws s3 sync repos_bedrock/ s3://aws-repos-data-039920874011-us-west-2/repos_bedrock/ --region us-west-2

# Verify upload
aws s3 ls s3://aws-repos-data-039920874011-us-west-2/repos_bedrock/ --recursive | wc -l
```

### Step 4: Start Ingestion Job

Trigger the Knowledge Base to ingest the new data:

```bash
# Start ingestion job
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id TOJENJXGHW \
  --data-source-id NRTZFOH2YX \
  --region us-west-2
```

**Response**: You'll get an ingestion job ID to track progress.

### Step 5: Monitor Progress

Monitor the ingestion progress:

```bash
# Using monitoring script
python3 monitor_ingestion.py

# Or manually check status
aws bedrock-agent get-ingestion-job \
  --knowledge-base-id TOJENJXGHW \
  --data-source-id NRTZFOH2YX \
  --ingestion-job-id INGESTION_JOB_ID \
  --region us-west-2
```

**Expected Timeline**: 10-30 minutes depending on number of repositories.

### Step 6: Verify Update

Test the chatbot to ensure new data is available:

1. Visit: https://d34pzvxmidb6ha.cloudfront.net
2. Ask about repositories that should be in your new data
3. Verify responses include new repositories

## Troubleshooting

### Common Issues

**Object Mapping Errors**:
- Ensure you used `convert_to_bedrock_format.py` script
- Check that JSON files have "text" and "metadata" structure
- Verify no flat JSON structure remains

**Ingestion Failures**:
- Check S3 upload completed successfully
- Verify CSV has all required columns
- Monitor ingestion job for specific error messages

**No New Data in Responses**:
- Wait for ingestion to complete (status: COMPLETE)
- Clear browser cache
- Test with specific repository names from new data

### Monitoring Commands

```bash
# Check ingestion status
aws bedrock-agent list-ingestion-jobs \
  --knowledge-base-id TOJENJXGHW \
  --data-source-id NRTZFOH2YX \
  --region us-west-2

# Check S3 data
aws s3 ls s3://aws-repos-data-039920874011-us-west-2/repos_bedrock/ --recursive

# Check OpenSearch collection
aws opensearchserverless list-collections --region us-west-2
```

## Automation Script

For frequent updates, create an automation script:

```bash
#!/bin/bash
# update-kb.sh

set -e

CSV_FILE="$1"
if [ -z "$CSV_FILE" ]; then
    echo "Usage: $0 <csv_file>"
    exit 1
fi

echo "🔄 Starting Knowledge Base update..."

# Step 1: Replace CSV
cp "$CSV_FILE" classification_results_awslabs.csv
echo "✅ CSV file updated"

# Step 2: Convert to Bedrock format
python3 convert_to_bedrock_format.py
echo "✅ Converted to Bedrock format"

# Step 3: Upload to S3
aws s3 sync repos_bedrock/ s3://aws-repos-data-039920874011-us-west-2/repos_bedrock/ --region us-west-2
echo "✅ Uploaded to S3"

# Step 4: Start ingestion
INGESTION_RESPONSE=$(aws bedrock-agent start-ingestion-job \
  --knowledge-base-id TOJENJXGHW \
  --data-source-id NRTZFOH2YX \
  --region us-west-2)

INGESTION_JOB_ID=$(echo $INGESTION_RESPONSE | jq -r '.ingestionJob.ingestionJobId')
echo "✅ Started ingestion job: $INGESTION_JOB_ID"

# Step 5: Monitor progress
echo "🔍 Monitoring progress..."
python3 monitor_ingestion.py

echo "🎉 Knowledge Base update complete!"
```

Usage:
```bash
chmod +x update-kb.sh
./update-kb.sh new_repositories.csv
```

## Best Practices

1. **Backup**: Always backup existing CSV before replacing
2. **Validation**: Verify CSV format and required columns
3. **Testing**: Test with small datasets first
4. **Monitoring**: Always monitor ingestion completion
5. **Verification**: Test chatbot responses after updates

## Data Format Requirements

### CSV Structure
- UTF-8 encoding
- Comma-separated values
- Header row with exact column names
- No empty repository names or URLs

### Content Guidelines
- **Descriptions**: Clear, concise repository descriptions
- **AWS Services**: Use standard AWS service names
- **Languages**: Use standard language names (Python, JavaScript, etc.)
- **Setup Time**: Use consistent format ("Quick Setup (< 1 hour)")
- **Cost Range**: Use consistent ranges ("Low ($10-100/month)")

## Cost Considerations

**Ingestion Costs**:
- Embeddings: ~$0.01 per 1000 repositories
- OpenSearch Serverless: ~$1-2/month for storage
- Total: Minimal cost for updates

**Optimization**:
- Batch updates rather than frequent small changes
- Remove duplicate or outdated repositories
- Monitor billing alerts

---

**Last Updated**: 2025-10-26  
**Knowledge Base ID**: TOJENJXGHW  
**Data Source ID**: NRTZFOH2YX  
**S3 Bucket**: aws-repos-data-039920874011-us-west-2
