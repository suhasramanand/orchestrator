terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# DynamoDB Tables
resource "aws_dynamodb_table" "jobs" {
  name           = "${var.project_name}-${var.environment}-jobs"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name           = "status-index"
    hash_key       = "status"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-jobs"
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "tasks" {
  name           = "${var.project_name}-${var.environment}-tasks"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "job_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name           = "job-id-index"
    hash_key       = "job_id"
    projection_type = "ALL"
  }

  global_secondary_index {
    name           = "status-index"
    hash_key       = "status"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-tasks"
    Environment = var.environment
  }
}

# SQS Queue for tasks
resource "aws_sqs_queue" "tasks" {
  name                      = "${var.project_name}-${var.environment}-tasks"
  visibility_timeout_seconds = var.sqs_visibility_timeout
  message_retention_seconds  = var.sqs_message_retention_period
  receive_wait_time_seconds  = 20  # Long polling

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.tasks_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name        = "${var.project_name}-tasks-queue"
    Environment = var.environment
  }
}

# Dead Letter Queue
resource "aws_sqs_queue" "tasks_dlq" {
  name                      = "${var.project_name}-${var.environment}-tasks-dlq"
  message_retention_seconds  = 1209600  # 14 days

  tags = {
    Name        = "${var.project_name}-tasks-dlq"
    Environment = var.environment
  }
}

# IAM Role for Lambda functions
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-${var.environment}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for Lambda
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-${var.environment}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.jobs.arn,
          "${aws_dynamodb_table.jobs.arn}/index/*",
          aws_dynamodb_table.tasks.arn,
          "${aws_dynamodb_table.tasks.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          aws_sqs_queue.tasks.arn,
          aws_sqs_queue.tasks_dlq.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "states:StartExecution"
        ]
        Resource = aws_sfn_state_machine.job_workflow.arn
      }
    ]
  })
}

# IAM Role for Step Functions
resource "aws_iam_role" "sfn_role" {
  name = "${var.project_name}-${var.environment}-sfn-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for Step Functions
resource "aws_iam_role_policy" "sfn_policy" {
  name = "${var.project_name}-${var.environment}-sfn-policy"
  role = aws_iam_role.sfn_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.create_tasks.arn,
          aws_lambda_function.monitor_completion.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.tasks.arn
      }
    ]
  })
}

# Lambda function to create tasks
resource "aws_lambda_function" "create_tasks" {
  filename         = "create_tasks.zip"
  function_name    = "${var.project_name}-${var.environment}-create-tasks"
  role            = aws_iam_role.lambda_role.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  environment {
    variables = {
      JOBS_TABLE = aws_dynamodb_table.jobs.name
      TASKS_TABLE = aws_dynamodb_table.tasks.name
      SQS_QUEUE_URL = aws_sqs_queue.tasks.url
    }
  }

  # Note: In production, you would package and upload the Lambda code
  # This is a placeholder - you need to create the Lambda function code separately
}

# Lambda function to monitor job completion
resource "aws_lambda_function" "monitor_completion" {
  filename         = "monitor_completion.zip"
  function_name    = "${var.project_name}-${var.environment}-monitor-completion"
  role            = aws_iam_role.lambda_role.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  environment {
    variables = {
      JOBS_TABLE = aws_dynamodb_table.jobs.name
      TASKS_TABLE = aws_dynamodb_table.tasks.name
    }
  }
}

# Step Functions State Machine
resource "aws_sfn_state_machine" "job_workflow" {
  name     = "${var.project_name}-${var.environment}-workflow"
  role_arn = aws_iam_role.sfn_role.arn

  definition = jsonencode({
    Comment = "Job Orchestration Workflow"
    StartAt = "CreateTasks"
    States = {
      CreateTasks = {
        Type     = "Task"
        Resource = aws_lambda_function.create_tasks.arn
        Next     = "EnqueueTasks"
      }
      EnqueueTasks = {
        Type = "Task"
        Resource = "arn:aws:states:::sqs:sendMessage"
        Parameters = {
          QueueUrl = aws_sqs_queue.tasks.url
          MessageBody = {
            "task_id.$": "$.task_id"
            "job_id.$": "$.job_id"
            "task_index.$": "$.task_index"
            "parameters.$": "$.parameters"
          }
        }
        Next = "MonitorCompletion"
      }
      MonitorCompletion = {
        Type     = "Task"
        Resource = aws_lambda_function.monitor_completion.arn
        Next     = "CheckCompletion"
      }
      CheckCompletion = {
        Type = "Choice"
        Choices = [
          {
            Variable      = "$.all_complete"
            BooleanEquals = true
            Next          = "JobCompleted"
          }
        ]
        Default = "WaitAndRetry"
      }
      WaitAndRetry = {
        Type    = "Wait"
        Seconds = 10
        Next    = "MonitorCompletion"
      }
      JobCompleted = {
        Type = "Succeed"
      }
    }
  })
}

# API Gateway (optional - you might use ALB instead)
# This is a basic setup - you'd need to configure routes and integrations

