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

