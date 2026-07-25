# coding: utf-8
"""
Lambda: agendamento-cancelamento-processor

Le mensagens da fila SQS agendamento-cancelamento e cria/atualiza
eventos no EventBridge Scheduler para que o cancelamento seja efetivado
na data correta.

Payload esperado:
{
    "id_boleto_individual": "<uuid>",
    "data_baixa_automatica": "2026-08-10",
    "tipo": "AGENDAR_CANCELAMENTO" | "EDITAR_DATA_CANCELAMENTO"
}

Estrategia de erros:
- Em caso de falha, a excecao sobe para o runtime do Lambda.
- O SQS torna a mensagem visivel novamente apos o visibility_timeout (5 min).
- Apos 3 tentativas, a mensagem vai para a DLQ.
- NAO fazer try/except silencioso - deixar o Lambda falhar para o SQS retentar.
"""

import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

scheduler_client = boto3.client("scheduler")

EFETIVAR_CANCELAMENTO_QUEUE_ARN = os.environ["EFETIVAR_CANCELAMENTO_QUEUE_ARN"]
SCHEDULER_ROLE_ARN = os.environ["SCHEDULER_ROLE_ARN"]
SCHEDULE_GROUP_NAME = os.environ.get("SCHEDULE_GROUP_NAME", "cancelamento-boletos")

TIPO_AGENDAR = "AGENDAR_CANCELAMENTO"
TIPO_EDITAR = "EDITAR_DATA_CANCELAMENTO"


def lambda_handler(event, context):
    records = event.get("Records", [])
    logger.info("Iniciando processamento. total_mensagens=%d", len(records))

    for record in records:
        _processar_registro(record)

    logger.info("Processamento finalizado com sucesso.")
    return {"statusCode": 200}


def _processar_registro(record):
    body = json.loads(record["body"])
    logger.info("Mensagem recebida: %s", json.dumps(body))

    _validar_payload(body)

    tipo = body["tipo"]
    id_boleto = body["id_boleto_individual"]
    data_baixa = body["data_baixa_automatica"]

    # Nome do schedule usa o id do boleto como chave idempotente
    schedule_name = f"cancelamento-{id_boleto}"

    # Agenda para as 03:00 UTC = meia-noite em Brasilia (UTC-3)
    schedule_expression = f"at({data_baixa}T03:00:00)"

    logger.info(
        "Processando. tipo=%s id_boleto=%s schedule_name=%s schedule_expression=%s",
        tipo, id_boleto, schedule_name, schedule_expression,
    )

    if tipo == TIPO_AGENDAR:
        _criar_agendamento(schedule_name, schedule_expression, body)
    elif tipo == TIPO_EDITAR:
        _editar_agendamento(schedule_name, schedule_expression, body)
    else:
        raise ValueError(f"Tipo de mensagem desconhecido: '{tipo}'")


def _schedule_params(schedule_name, schedule_expression, payload):
    return dict(
        Name=schedule_name,
        GroupName=SCHEDULE_GROUP_NAME,
        ScheduleExpression=schedule_expression,
        ScheduleExpressionTimezone="America/Sao_Paulo",
        FlexibleTimeWindow={"Mode": "OFF"},
        Target={
            "Arn": EFETIVAR_CANCELAMENTO_QUEUE_ARN,
            "RoleArn": SCHEDULER_ROLE_ARN,
            "Input": json.dumps(payload),
        },
        ActionAfterCompletion="DELETE",
    )


def _criar_agendamento(schedule_name, schedule_expression, payload):
    try:
        scheduler_client.create_schedule(**_schedule_params(schedule_name, schedule_expression, payload))
        logger.info("Schedule criado com sucesso. name=%s", schedule_name)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "ConflictException":
            logger.warning("Schedule ja existe, atualizando. name=%s", schedule_name)
            _editar_agendamento(schedule_name, schedule_expression, payload)
        else:
            logger.error("Erro ao criar schedule. name=%s error=%s", schedule_name, e)
            raise


def _editar_agendamento(schedule_name, schedule_expression, payload):
    try:
        scheduler_client.update_schedule(**_schedule_params(schedule_name, schedule_expression, payload))
        logger.info("Schedule atualizado com sucesso. name=%s", schedule_name)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "ResourceNotFoundException":
            logger.warning("Schedule nao encontrado, criando. name=%s", schedule_name)
            _criar_agendamento(schedule_name, schedule_expression, payload)
        else:
            logger.error("Erro ao atualizar schedule. name=%s error=%s", schedule_name, e)
            raise


def _validar_payload(body):
    campos_obrigatorios = ["tipo", "id_boleto_individual", "data_baixa_automatica"]
    ausentes = [c for c in campos_obrigatorios if not body.get(c)]
    if ausentes:
        raise ValueError(
            f"Payload invalido. Campos ausentes: {ausentes}. Body: {body}"
        )

