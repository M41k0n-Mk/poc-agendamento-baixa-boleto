# ===========================================================================
# Lambda — agendamento-cancelamento-processor
#
# Lê a fila `agendamento-cancelamento` e cria/atualiza schedules no
# EventBridge Scheduler de acordo com o campo `tipo` da mensagem.
# ===========================================================================

# ---------------------------------------------------------------------------
# Empacota o código Python como .zip para deploy
# ---------------------------------------------------------------------------
data "archive_file" "agendamento_processor_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../lambda/agendamento-cancelamento-processor"
  output_path = "${path.root}/.terraform/agendamento-cancelamento-processor.zip"
  excludes    = ["tests", "tests/*", "__pycache__", "*.pyc", "requirements.txt"]
}

# ---------------------------------------------------------------------------
# IAM Role — Lambda execution role
# ---------------------------------------------------------------------------
resource "aws_iam_role" "lambda_agendamento_processor" {
  name = "${local.prefix}-agendamento-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_agendamento_processor.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Permissões customizadas: SQS + EventBridge Scheduler
resource "aws_iam_role_policy" "lambda_agendamento_policy" {
  name = "${local.prefix}-agendamento-processor-policy"
  role = aws_iam_role.lambda_agendamento_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # ── SQS: ler e deletar mensagens da fila principal ──────────────────
      {
        Sid    = "SqsConsumir"
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
        ]
        Resource = aws_sqs_queue.agendamento_cancelamento.arn
      },
      # ── EventBridge Scheduler: gerenciar schedules ───────────────────────
      {
        Sid    = "SchedulerGerenciar"
        Effect = "Allow"
        Action = [
          "scheduler:CreateSchedule",
          "scheduler:UpdateSchedule",
          "scheduler:GetSchedule",
          "scheduler:DeleteSchedule",
        ]
        Resource = "arn:aws:scheduler:${var.aws_region}:*:schedule/${aws_scheduler_schedule_group.cancelamento_boletos.name}/*"
      },
      # ── IAM PassRole: permitir que o Lambda passe a role pro Scheduler ──
      {
        Sid      = "PassRoleScheduler"
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = aws_iam_role.scheduler_to_sqs.arn
      }
    ]
  })
}

# ---------------------------------------------------------------------------
# IAM Role — EventBridge Scheduler → SQS efetivar-cancelamento
# Esta role é assumida pelo EventBridge Scheduler para postar na fila.
# ---------------------------------------------------------------------------
resource "aws_iam_role" "scheduler_to_sqs" {
  name = "${local.prefix}-scheduler-to-sqs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "scheduler_to_sqs_policy" {
  name = "${local.prefix}-scheduler-to-sqs-policy"
  role = aws_iam_role.scheduler_to_sqs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid      = "SqsEnviarMensagem"
      Effect   = "Allow"
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.efetivar_cancelamento.arn
    }]
  })
}

# ---------------------------------------------------------------------------
# EventBridge Scheduler — Schedule Group
# Agrupa todos os schedules de cancelamento de boletos.
# ---------------------------------------------------------------------------
resource "aws_scheduler_schedule_group" "cancelamento_boletos" {
  name = "${local.prefix}-cancelamento-boletos"
}

# ---------------------------------------------------------------------------
# Lambda Function
# ---------------------------------------------------------------------------
resource "aws_lambda_function" "agendamento_cancelamento_processor" {
  function_name = "${local.prefix}-agendamento-processor"
  description   = "Processa eventos de agendamento/edição de cancelamento de boletos e cria schedules no EventBridge Scheduler."

  filename         = data.archive_file.agendamento_processor_zip.output_path
  source_code_hash = data.archive_file.agendamento_processor_zip.output_base64sha256

  runtime = "python3.12"
  handler = "handler.lambda_handler"

  role = aws_iam_role.lambda_agendamento_processor.arn

  # Timeout maior que o batch window para evitar cortes durante processamento
  timeout     = 60  # segundos
  memory_size = 128 # MB — suficiente para este workload

  environment {
    variables = {
      EFETIVAR_CANCELAMENTO_QUEUE_ARN = aws_sqs_queue.efetivar_cancelamento.arn
      SCHEDULER_ROLE_ARN              = aws_iam_role.scheduler_to_sqs.arn
      SCHEDULE_GROUP_NAME             = aws_scheduler_schedule_group.cancelamento_boletos.name
    }
  }
}

# ---------------------------------------------------------------------------
# SQS Event Source Mapping — Liga a fila ao Lambda
# ---------------------------------------------------------------------------
resource "aws_lambda_event_source_mapping" "agendamento_cancelamento_trigger" {
  event_source_arn = aws_sqs_queue.agendamento_cancelamento.arn
  function_name    = aws_lambda_function.agendamento_cancelamento_processor.arn

  # Processa 1 mensagem por vez para facilitar o controle de erros e retries
  batch_size = 1

  # Respeita o visibility_timeout da fila (300s = 5 min entre retries)
  # O Lambda não confirma a mensagem se lançar exceção — SQS reenfileira
  function_response_types = ["ReportBatchItemFailures"]
}

# ===========================================================================
# Lambda — efetivar-cancelamento-processor
#
# Lê a fila `efetivar-cancelamento` (postada pelo EventBridge Scheduler
# na data agendada) e efetiva o cancelamento chamando a API externa.
# ===========================================================================

data "archive_file" "efetivar_processor_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../lambda/efetivar-cancelamento-processor"
  output_path = "${path.root}/.terraform/efetivar-cancelamento-processor.zip"
  excludes    = ["tests", "tests/*", "__pycache__", "*.pyc", "requirements.txt"]
}

# ---------------------------------------------------------------------------
# IAM Role — Lambda efetivar execution role
# ---------------------------------------------------------------------------
resource "aws_iam_role" "lambda_efetivar_processor" {
  name = "${local.prefix}-efetivar-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_efetivar_basic_execution" {
  role       = aws_iam_role.lambda_efetivar_processor.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_efetivar_policy" {
  name = "${local.prefix}-efetivar-processor-policy"
  role = aws_iam_role.lambda_efetivar_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "SqsConsumir"
      Effect = "Allow"
      Action = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
      ]
      Resource = aws_sqs_queue.efetivar_cancelamento.arn
    }]
  })
}

# ---------------------------------------------------------------------------
# Lambda Function
# ---------------------------------------------------------------------------
resource "aws_lambda_function" "efetivar_cancelamento_processor" {
  function_name = "${local.prefix}-efetivar-cancelamento-processor"
  description   = "Efetiva o cancelamento do boleto na data agendada, chamando a API externa."

  filename         = data.archive_file.efetivar_processor_zip.output_path
  source_code_hash = data.archive_file.efetivar_processor_zip.output_base64sha256

  runtime = "python3.12"
  handler = "handler.lambda_handler"

  role = aws_iam_role.lambda_efetivar_processor.arn

  timeout     = 60
  memory_size = 128

  environment {
    variables = {
      # URL da API externa de cancelamento — preencher quando disponível
      API_CANCELAMENTO_URL = var.api_cancelamento_url
    }
  }
}

# ---------------------------------------------------------------------------
# SQS Event Source Mapping — Liga a fila efetivar ao Lambda
# ---------------------------------------------------------------------------
resource "aws_lambda_event_source_mapping" "efetivar_cancelamento_trigger" {
  event_source_arn = aws_sqs_queue.efetivar_cancelamento.arn
  function_name    = aws_lambda_function.efetivar_cancelamento_processor.arn

  # 1 mensagem por vez — se a chamada à API falhar, só essa mensagem é reprocessada
  batch_size = 1

  # Respeita o visibility_timeout da fila (3600s = 1 hora entre retries)
  function_response_types = ["ReportBatchItemFailures"]
}

