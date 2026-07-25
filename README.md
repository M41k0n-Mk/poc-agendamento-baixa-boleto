# POC — Agendamento de Baixa Automática de Boleto

## Visão Geral da Arquitetura

```
Frontend
   │
   ▼
[App Java — local ou ECS]
   │  POST /api/v1/agendamentos
   │  PATCH /api/v1/agendamentos
   │
   ▼
[SQS: agendamento-cancelamento]  ◄── fila principal
   │  3 tentativas · intervalo de 5 min · DLQ
   │
   ▼
[Lambda — ouve a fila, lê o campo "tipo"]
   ├── AGENDAR_CANCELAMENTO     → cria evento no EventBridge Scheduler
   └── EDITAR_DATA_CANCELAMENTO → atualiza evento no EventBridge Scheduler
                                          │
                                          ▼ (na data agendada)
                               [SQS: efetivar-cancelamento]
                                          │  3 tentativas · intervalo de 1h · DLQ
                                          │
                                          ▼
                               [Lambda — chama API externa p/ cancelar o boleto]
```

## Estrutura do Repositório

```
├── app/          → Aplicação Java (Spring Boot)
└── infra/        → Infraestrutura AWS (Terraform)
```

---

## Pré-requisitos

| Ferramenta | Versão mínima |
|------------|---------------|
| Java       | 21            |
| Maven      | 3.9+          |
| Terraform  | 1.5+          |
| AWS CLI    | 2.x           |

---

## 1 — Configurar credenciais AWS localmente

Configure o AWS CLI com um usuário/role que tenha permissão para criar filas SQS:

```bash
aws configure
# AWS Access Key ID: <sua_access_key>
# AWS Secret Access Key: <sua_secret_key>
# Default region name: sa-east-1
# Default output format: json
```

---

## 2 — Provisionar as filas SQS na AWS (Terraform)

```bash
cd infra

terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

Após o apply, copie a URL da fila principal exibida no output:

```
Outputs:
  agendamento_cancelamento_queue_url = "https://sqs.sa-east-1.amazonaws.com/123456789012/poc-agendamento-baixa-boleto-dev-agendamento-cancelamento"
```

---

## 3 — Rodar a aplicação Java localmente

Defina a variável de ambiente com a URL copiada acima e suba a app:

**Windows (PowerShell):**
```powershell
$env:SQS_AGENDAMENTO_CANCELAMENTO_URL = "https://sqs.sa-east-1.amazonaws.com/123456789012/poc-agendamento-baixa-boleto-dev-agendamento-cancelamento"
cd app
./mvnw spring-boot:run
```

**Linux / macOS:**
```bash
export SQS_AGENDAMENTO_CANCELAMENTO_URL="https://sqs.sa-east-1.amazonaws.com/..."
cd app
./mvnw spring-boot:run
```

A aplicação sobe em `http://localhost:8080`.

---

## 4 — Endpoints

### Criar agendamento de cancelamento
```http
POST /api/v1/agendamentos
Content-Type: application/json

{
  "id_boleto_individual": "550e8400-e29b-41d4-a716-446655440000",
  "data_baixa_automatica": "2026-08-10"
}
```
**Response:** `201 Created`

---

### Editar data de cancelamento
```http
PATCH /api/v1/agendamentos
Content-Type: application/json

{
  "id_boleto_individual": "550e8400-e29b-41d4-a716-446655440000",
  "data_baixa_automatica": "2026-09-15"
}
```
**Response:** `200 OK`

---

## Payload enviado para a fila SQS

```json
{
  "data_baixa_automatica": "2026-08-10",
  "tipo": "AGENDAR_CANCELAMENTO",
  "id_boleto_individual": "550e8400-e29b-41d4-a716-446655440000"
}
```

O campo `tipo` pode ser:
- `AGENDAR_CANCELAMENTO`
- `EDITAR_DATA_CANCELAMENTO`

---

## Filas SQS — Estratégia de Retry

| Fila                         | Tentativas | Intervalo   | DLQ | Retenção DLQ |
|------------------------------|-----------|-------------|-----|--------------|
| `agendamento-cancelamento`   | 3         | 5 minutos   | ✅  | 14 dias      |
| `efetivar-cancelamento`      | 3         | 1 hora      | ✅  | 14 dias      |

> O intervalo é controlado pelo `visibility_timeout_seconds` da fila. O consumer (Lambda) **não deve** deletar a mensagem em caso de falha — ela volta automaticamente para a fila após o timeout.

