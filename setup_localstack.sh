#!/bin/bash
set -e

echo "🚀 Setting up LocalStack SQS"
echo "============================"
echo ""

# Wait for LocalStack to be ready
echo "⏳ Waiting for LocalStack to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:4566/_localstack/health | grep -q '"sqs": "available"'; then
        echo "✅ LocalStack is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ LocalStack failed to start"
        exit 1
    fi
    sleep 2
done

echo ""
echo "📦 Creating SQS queue..."

# Create SQS queue
aws --endpoint-url=http://localhost:4566 sqs create-queue \
    --queue-name tasks \
    --region us-east-1 2>&1 | grep -v "deprecated" || true

# Get queue URL
QUEUE_URL=$(aws --endpoint-url=http://localhost:4566 sqs get-queue-url \
    --queue-name tasks \
    --region us-east-1 \
    --query 'QueueUrl' \
    --output text 2>/dev/null)

if [ -z "$QUEUE_URL" ]; then
    echo "❌ Failed to create queue"
    exit 1
fi

echo "✅ Queue created: $QUEUE_URL"
echo ""

# Create DLQ
echo "📦 Creating Dead Letter Queue..."
aws --endpoint-url=http://localhost:4566 sqs create-queue \
    --queue-name tasks-dlq \
    --region us-east-1 2>&1 | grep -v "deprecated" || true

DLQ_URL=$(aws --endpoint-url=http://localhost:4566 sqs get-queue-url \
    --queue-name tasks-dlq \
    --region us-east-1 \
    --query 'QueueUrl' \
    --output text 2>/dev/null)

echo "✅ DLQ created: $DLQ_URL"
echo ""

# Get DLQ ARN for redrive policy
DLQ_ARN=$(aws --endpoint-url=http://localhost:4566 sqs get-queue-attributes \
    --queue-url "$DLQ_URL" \
    --attribute-names QueueArn \
    --region us-east-1 \
    --query 'Attributes.QueueArn' \
    --output text 2>/dev/null)

# Configure redrive policy
echo "🔧 Configuring redrive policy..."
aws --endpoint-url=http://localhost:4566 sqs set-queue-attributes \
    --queue-url "$QUEUE_URL" \
    --attributes "{\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_ARN\\\",\\\"maxReceiveCount\\\":3}\"}" \
    --region us-east-1 2>&1 | grep -v "deprecated" || true

echo "✅ Redrive policy configured"
echo ""

echo "📊 Queue Information:"
echo "  Main Queue: $QUEUE_URL"
echo "  DLQ: $DLQ_URL"
echo ""

# Test sending a message
echo "🧪 Testing queue..."
aws --endpoint-url=http://localhost:4566 sqs send-message \
    --queue-url "$QUEUE_URL" \
    --message-body '{"test": "message"}' \
    --region us-east-1 2>&1 | grep -v "deprecated" || true

echo "✅ Test message sent"
echo ""

echo "✅ LocalStack SQS setup complete!"
echo ""
echo "📝 Queue URL for workers: $QUEUE_URL"
