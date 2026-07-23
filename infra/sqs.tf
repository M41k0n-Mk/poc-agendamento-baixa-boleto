# ---------------------------------------------------------------------------
# Locals
# ---------------------------------------------------------------------------
locals {
  # Naming convention: {project}-{name}-{environment}
  prefix = "${var.project}-${var.environment}"
}

# ===========================================================================
# QUEUE 1 — agendamento-cancelamento
# Receives AGENDAR_CANCELAMENTO and EDITAR_DATA_CANCELAMENTO events.
# A Lambda reads this queue and communicates with EventBridge Scheduler.
#
# Retry strategy: 3 attempts, 5-minute intervals
#   → visibility_timeout_seconds = 300 (5 min)
#   → maxReceiveCount            = 3
# ===========================================================================

resource "aws_sqs_queue" "agendamento_cancelamento_dlq" {
  name = "${local.prefix}-agendamento-cancelamento-dlq"

  # Messages in DLQ are retained for 14 days for investigation
  message_retention_seconds = 1209600 # 14 days

  sqs_managed_sse_enabled = true
}

resource "aws_sqs_queue" "agendamento_cancelamento" {
  name = "${local.prefix}-agendamento-cancelamento"

  # Controls the retry interval: message becomes visible again after 5 minutes
  visibility_timeout_seconds = 300 # 5 minutes

  # Max message lifetime in the queue
  message_retention_seconds = 86400 # 1 day

  # Maximum size of a message (256 KB is the SQS max)
  max_message_size = 262144

  # Long polling: reduces empty receives and cost
  receive_wait_time_seconds = 20

  sqs_managed_sse_enabled = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.agendamento_cancelamento_dlq.arn
    maxReceiveCount     = 3
  })
}

# Allow the DLQ to receive messages from the main queue (redrive allow policy)
resource "aws_sqs_queue_redrive_allow_policy" "agendamento_cancelamento_dlq" {
  queue_url = aws_sqs_queue.agendamento_cancelamento_dlq.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.agendamento_cancelamento.arn]
  })
}

# ===========================================================================
# QUEUE 2 — efetivar-cancelamento
# EventBridge Scheduler posts here on the scheduled date.
# A Lambda reads this queue and calls the external boleto cancellation API.
#
# Retry strategy: 3 attempts, 1-hour intervals
#   → visibility_timeout_seconds = 3600 (1 hour)
#   → maxReceiveCount            = 3
# ===========================================================================

resource "aws_sqs_queue" "efetivar_cancelamento_dlq" {
  name = "${local.prefix}-efetivar-cancelamento-dlq"

  # Messages in DLQ are retained for 14 days for investigation
  message_retention_seconds = 1209600 # 14 days

  sqs_managed_sse_enabled = true
}

resource "aws_sqs_queue" "efetivar_cancelamento" {
  name = "${local.prefix}-efetivar-cancelamento"

  # Controls the retry interval: message becomes visible again after 1 hour
  visibility_timeout_seconds = 3600 # 1 hour

  # Enough time to cover all 3 retries (3h) plus margin
  message_retention_seconds = 43200 # 12 hours

  max_message_size = 262144

  # Long polling
  receive_wait_time_seconds = 20

  sqs_managed_sse_enabled = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.efetivar_cancelamento_dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sqs_queue_redrive_allow_policy" "efetivar_cancelamento_dlq" {
  queue_url = aws_sqs_queue.efetivar_cancelamento_dlq.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.efetivar_cancelamento.arn]
  })
}

