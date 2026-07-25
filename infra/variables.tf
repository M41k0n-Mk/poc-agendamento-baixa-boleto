variable "aws_region" {
  description = "AWS region where resources will be created"
  type        = string
  default     = "sa-east-1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "project" {
  description = "Project name used for naming and tagging resources"
  type        = string
  default     = "poc-agendamento-baixa-boleto"
}

variable "api_cancelamento_url" {
  description = "URL da API externa que efetiva o cancelamento do boleto. Deixar vazio até a API estar disponível."
  type        = string
  default     = ""
}

