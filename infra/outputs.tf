# ---------------------------------------------------------------------------
# Queue 1 — agendamento-cancelamento
# ---------------------------------------------------------------------------
output "agendamento_cancelamento_queue_url" {
  description = "URL of the agendamento-cancelamento main queue"
  value       = aws_sqs_queue.agendamento_cancelamento.url
}

output "agendamento_cancelamento_queue_arn" {
  description = "ARN of the agendamento-cancelamento main queue"
  value       = aws_sqs_queue.agendamento_cancelamento.arn
}

output "agendamento_cancelamento_dlq_url" {
  description = "URL of the agendamento-cancelamento dead-letter queue"
  value       = aws_sqs_queue.agendamento_cancelamento_dlq.url
}

output "agendamento_cancelamento_dlq_arn" {
  description = "ARN of the agendamento-cancelamento dead-letter queue"
  value       = aws_sqs_queue.agendamento_cancelamento_dlq.arn
}

# ---------------------------------------------------------------------------
# Queue 2 — efetivar-cancelamento
# ---------------------------------------------------------------------------
output "efetivar_cancelamento_queue_url" {
  description = "URL of the efetivar-cancelamento main queue"
  value       = aws_sqs_queue.efetivar_cancelamento.url
}

output "efetivar_cancelamento_queue_arn" {
  description = "ARN of the efetivar-cancelamento main queue"
  value       = aws_sqs_queue.efetivar_cancelamento.arn
}

output "efetivar_cancelamento_dlq_url" {
  description = "URL of the efetivar-cancelamento dead-letter queue"
  value       = aws_sqs_queue.efetivar_cancelamento_dlq.url
}

output "efetivar_cancelamento_dlq_arn" {
  description = "ARN of the efetivar-cancelamento dead-letter queue"
  value       = aws_sqs_queue.efetivar_cancelamento_dlq.arn
}

# ---------------------------------------------------------------------------
# Lambda — agendamento-cancelamento-processor
# ---------------------------------------------------------------------------
output "lambda_agendamento_processor_name" {
  description = "Name of the agendamento-cancelamento Lambda function"
  value       = aws_lambda_function.agendamento_cancelamento_processor.function_name
}

output "lambda_agendamento_processor_arn" {
  description = "ARN of the agendamento-cancelamento Lambda function"
  value       = aws_lambda_function.agendamento_cancelamento_processor.arn
}

output "lambda_efetivar_processor_name" {
  description = "Name of the efetivar-cancelamento Lambda function"
  value       = aws_lambda_function.efetivar_cancelamento_processor.function_name
}

output "lambda_efetivar_processor_arn" {
  description = "ARN of the efetivar-cancelamento Lambda function"
  value       = aws_lambda_function.efetivar_cancelamento_processor.arn
}

# ---------------------------------------------------------------------------
# EventBridge Scheduler Group
# ---------------------------------------------------------------------------
output "scheduler_group_name" {
  description = "Name of the EventBridge Scheduler group for cancelamento-boletos"
  value       = aws_scheduler_schedule_group.cancelamento_boletos.name
}

output "scheduler_role_arn" {
  description = "ARN of the IAM role used by EventBridge Scheduler to post to efetivar-cancelamento queue"
  value       = aws_iam_role.scheduler_to_sqs.arn
}

