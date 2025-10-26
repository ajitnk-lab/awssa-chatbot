#!/bin/bash

# Setup CloudWatch monitoring and cost alerts for AWS Solutions Architect Agent

set -e

REGION="us-west-2"
STACK_NAME="AwsReposAgentStack"
EMAIL="your-email@example.com"  # Update this with your email

echo "📊 Setting up monitoring and cost alerts..."

# Function to create cost budget
create_cost_budget() {
    echo "💰 Creating cost budget..."
    
    # Create budget for $50 monthly limit
    aws budgets create-budget \
        --account-id $(aws sts get-caller-identity --query Account --output text) \
        --budget '{
            "BudgetName": "AWS-Repos-Agent-Budget",
            "BudgetLimit": {
                "Amount": "50.0",
                "Unit": "USD"
            },
            "TimeUnit": "MONTHLY",
            "BudgetType": "COST",
            "CostFilters": {
                "TagKey": ["aws:cloudformation:stack-name"],
                "TagValue": ["'$STACK_NAME'"]
            }
        }' \
        --notifications-with-subscribers '[
            {
                "Notification": {
                    "NotificationType": "ACTUAL",
                    "ComparisonOperator": "GREATER_THAN",
                    "Threshold": 80.0,
                    "ThresholdType": "PERCENTAGE"
                },
                "Subscribers": [
                    {
                        "SubscriptionType": "EMAIL",
                        "Address": "'$EMAIL'"
                    }
                ]
            },
            {
                "Notification": {
                    "NotificationType": "FORECASTED",
                    "ComparisonOperator": "GREATER_THAN",
                    "Threshold": 100.0,
                    "ThresholdType": "PERCENTAGE"
                },
                "Subscribers": [
                    {
                        "SubscriptionType": "EMAIL",
                        "Address": "'$EMAIL'"
                    }
                ]
            }
        ]' \
        --region us-east-1  # Budgets API is only available in us-east-1
    
    echo "✅ Cost budget created with $50 monthly limit"
}

# Function to create CloudWatch dashboard
create_dashboard() {
    echo "📈 Creating CloudWatch dashboard..."
    
    # Get Lambda function name
    FUNCTION_NAME="$STACK_NAME-AgentFunction"
    
    # Create dashboard
    aws cloudwatch put-dashboard \
        --dashboard-name "AWS-Repos-Agent-Dashboard" \
        --dashboard-body '{
            "widgets": [
                {
                    "type": "metric",
                    "x": 0,
                    "y": 0,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            [ "AWS/Lambda", "Invocations", "FunctionName", "'$FUNCTION_NAME'" ],
                            [ ".", "Errors", ".", "." ],
                            [ ".", "Duration", ".", "." ]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": "'$REGION'",
                        "title": "Lambda Function Metrics"
                    }
                },
                {
                    "type": "metric",
                    "x": 0,
                    "y": 6,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            [ "AWS/ApiGateway", "Count", "ApiName", "AWS Repos Agent API" ],
                            [ ".", "4XXError", ".", "." ],
                            [ ".", "5XXError", ".", "." ],
                            [ ".", "Latency", ".", "." ]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": "'$REGION'",
                        "title": "API Gateway Metrics"
                    }
                },
                {
                    "type": "log",
                    "x": 0,
                    "y": 12,
                    "width": 24,
                    "height": 6,
                    "properties": {
                        "query": "SOURCE \"/aws/lambda/'$FUNCTION_NAME'\"\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 20",
                        "region": "'$REGION'",
                        "title": "Recent Errors"
                    }
                }
            ]
        }' \
        --region $REGION
    
    echo "✅ CloudWatch dashboard created"
}

# Function to create CloudWatch alarms
create_alarms() {
    echo "🚨 Creating CloudWatch alarms..."
    
    FUNCTION_NAME="$STACK_NAME-AgentFunction"
    
    # Lambda error rate alarm
    aws cloudwatch put-metric-alarm \
        --alarm-name "AWS-Repos-Agent-Lambda-Errors" \
        --alarm-description "Lambda function error rate is high" \
        --metric-name Errors \
        --namespace AWS/Lambda \
        --statistic Sum \
        --period 300 \
        --threshold 5 \
        --comparison-operator GreaterThanThreshold \
        --evaluation-periods 2 \
        --alarm-actions "arn:aws:sns:$REGION:$(aws sts get-caller-identity --query Account --output text):aws-repos-agent-alerts" \
        --dimensions Name=FunctionName,Value=$FUNCTION_NAME \
        --region $REGION
    
    # Lambda duration alarm
    aws cloudwatch put-metric-alarm \
        --alarm-name "AWS-Repos-Agent-Lambda-Duration" \
        --alarm-description "Lambda function duration is high" \
        --metric-name Duration \
        --namespace AWS/Lambda \
        --statistic Average \
        --period 300 \
        --threshold 25000 \
        --comparison-operator GreaterThanThreshold \
        --evaluation-periods 3 \
        --alarm-actions "arn:aws:sns:$REGION:$(aws sts get-caller-identity --query Account --output text):aws-repos-agent-alerts" \
        --dimensions Name=FunctionName,Value=$FUNCTION_NAME \
        --region $REGION
    
    # API Gateway 5XX errors alarm
    aws cloudwatch put-metric-alarm \
        --alarm-name "AWS-Repos-Agent-API-5XX-Errors" \
        --alarm-description "API Gateway 5XX error rate is high" \
        --metric-name 5XXError \
        --namespace AWS/ApiGateway \
        --statistic Sum \
        --period 300 \
        --threshold 3 \
        --comparison-operator GreaterThanThreshold \
        --evaluation-periods 2 \
        --alarm-actions "arn:aws:sns:$REGION:$(aws sts get-caller-identity --query Account --output text):aws-repos-agent-alerts" \
        --dimensions Name=ApiName,Value="AWS Repos Agent API" \
        --region $REGION
    
    echo "✅ CloudWatch alarms created"
}

# Function to create SNS topic for alerts
create_sns_topic() {
    echo "📧 Creating SNS topic for alerts..."
    
    # Create SNS topic
    TOPIC_ARN=$(aws sns create-topic \
        --name aws-repos-agent-alerts \
        --region $REGION \
        --query 'TopicArn' \
        --output text)
    
    # Subscribe email to topic
    aws sns subscribe \
        --topic-arn $TOPIC_ARN \
        --protocol email \
        --notification-endpoint $EMAIL \
        --region $REGION
    
    echo "✅ SNS topic created: $TOPIC_ARN"
    echo "📧 Please check your email and confirm the subscription"
}

# Main function
main() {
    echo "📊 AWS Solutions Architect Agent - Monitoring Setup"
    echo "=================================================="
    
    # Check if email is configured
    if [ "$EMAIL" = "your-email@example.com" ]; then
        echo "⚠️  Please update the EMAIL variable in this script with your email address"
        read -p "Enter your email address: " EMAIL
    fi
    
    echo "📧 Using email: $EMAIL"
    
    # Create monitoring resources
    create_sns_topic
    create_cost_budget
    create_dashboard
    create_alarms
    
    echo ""
    echo "✅ Monitoring setup complete!"
    echo ""
    echo "📊 Resources created:"
    echo "   • Cost budget with $50 monthly limit"
    echo "   • CloudWatch dashboard: AWS-Repos-Agent-Dashboard"
    echo "   • CloudWatch alarms for errors and performance"
    echo "   • SNS topic for email alerts"
    echo ""
    echo "🔗 Access your dashboard:"
    echo "   https://$REGION.console.aws.amazon.com/cloudwatch/home?region=$REGION#dashboards:name=AWS-Repos-Agent-Dashboard"
    echo ""
    echo "💡 Next steps:"
    echo "   1. Confirm your email subscription for alerts"
    echo "   2. Review the CloudWatch dashboard"
    echo "   3. Test the cost budget by checking AWS Budgets console"
}

# Run main function
main
