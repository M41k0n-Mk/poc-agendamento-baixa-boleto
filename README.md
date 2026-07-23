# poc-agendamento-baixa-boleto

POC de agendamento e baixa automática de boletos via AWS SQS + EventBridge Scheduler.

## Estrutura do repositório

```
poc-agendamento-baixa-boleto/
├── app/        # Aplicação Java (Spring Boot) — a ser implementada
└── infra/      # Infraestrutura AWS via Terraform
```

---

## Arquitetura (visão geral)

```
Frontend
   │
   ▼
[app/ — Spring Boot]
   │  POST /agendamentos        → cria agendamento
   │  PUT  /agendamentos/{id}   → edita data de agendamento
   │
   ▼
┌─────────────────────────────────────────────┐
│  SQS: agendamento-cancelamento              │  ← Fila principal
│  Retries: 3x | Intervalo: 5 min             │
│  DLQ: agendamento-cancelamento-dlq          │
└─────────────────────────────────────────────┘
   │
   ▼
[Lambda — ouve a fila, diferencia tipo pelo campo "tipo"]
   │  AGENDAR_CANCELAMENTO       → cria evento no EventBridge Scheduler
   │  EDITAR_DATA_CANCELAMENTO   → atualiza evento no EventBridge Scheduler
   │
   ▼
[EventBridge Scheduler — dispara na data_baixa_automatica]
   │
   ▼
┌─────────────────────────────────────────────┐
│  SQS: efetivar-cancelamento                 │  ← Fila de execução
│  Retries: 3x | Intervalo: 1 hora            │
│  DLQ: efetivar-cancelamento-dlq             │
└─────────────────────────────────────────────┘
   │
   ▼
[Lambda — efetiva o cancelamento via API externa]
```

### Payload da fila principal

```json
{
  "data_baixa_automatica": "2026-08-10",
  "tipo": "AGENDAR_CANCELAMENTO",
  "id_boleto_individual": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Valores possíveis para `tipo`:**
- `AGENDAR_CANCELAMENTO`
- `EDITAR_DATA_CANCELAMENTO`

---

## Infra — SQS

### Pré-requisitos

- [Terraform >= 1.5](https://developer.hashicorp.com/terraform/install)
- AWS CLI configurado (`aws configure`)

### Deploy

```bash
cd infra

# Inicializa os providers
terraform init

# Visualiza o plano de execução
terraform plan

# Aplica a infraestrutura
terraform apply
```

### Recursos criados

| Recurso | Nome (dev) |
|---|---|
| Fila principal | `poc-agendamento-baixa-boleto-dev-agendamento-cancelamento` |
| DLQ da fila principal | `poc-agendamento-baixa-boleto-dev-agendamento-cancelamento-dlq` |
| Fila de cancelamento | `poc-agendamento-baixa-boleto-dev-efetivar-cancelamento` |
| DLQ da fila de cancelamento | `poc-agendamento-baixa-boleto-dev-efetivar-cancelamento-dlq` |

### Configurações de retry

| Fila | Visibility Timeout | Max Receive Count | Comportamento |
|---|---|---|---|
| agendamento-cancelamento | 300s (5 min) | 3 | Após 3 falhas → DLQ |
| efetivar-cancelamento | 3600s (1 hora) | 3 | Após 3 falhas → DLQ |

> **Como funciona o retry no SQS:** o consumidor precisa deletar a mensagem após processá-la com sucesso. Se não deletar dentro do `visibility_timeout`, a mensagem fica visível novamente para reprocessamento. Após `maxReceiveCount` tentativas, vai para a DLQ.

---

## App — Java / Spring Boot

> A ser implementado nos próximos passos.

