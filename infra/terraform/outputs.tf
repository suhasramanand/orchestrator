output "jobs_table_name" {
  description = "DynamoDB jobs table name"
  value       = aws_dynamodb_table.jobs.name
}

output "tasks_table_name" {
  description = "DynamoDB tasks table name"
  value       = aws_dynamodb_table.tasks.name
}

output "sqs_queue_url" {
  description = "SQS task queue URL"
  value       = aws_sqs_queue.tasks.url
}

output "sqs_queue_arn" {
  description = "SQS task queue ARN"
  value       = aws_sqs_queue.tasks.arn
}

output "step_functions_arn" {
  description = "Step Functions state machine ARN"
  value       = aws_sfn_state_machine.job_workflow.arn
}

output "lambda_create_tasks_arn" {
  description = "Lambda function ARN for creating tasks"
  value       = aws_lambda_function.create_tasks.arn
}

output "lambda_monitor_completion_arn" {
  description = "Lambda function ARN for monitoring completion"
  value       = aws_lambda_function.monitor_completion.arn
}

