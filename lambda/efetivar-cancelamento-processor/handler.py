# coding: utf-8
"""
Lambda: efetivar-cancelamento-processor

Le mensagens da fila SQS efetivar-cancelamento, postadas pelo EventBridge
Scheduler na data agendada, e efetiva o cancelamento do boleto chamando
a API externa.

Payload esperado:
{
    "id_boleto_individual": "<uuid>",
    "data_baixa_automatica": "2026-08-10",
    "tipo": "AGENDAR_CANCELAMENTO" | "EDITAR_DATA_CANCELAMENTO"
}

Estrategia de erros:
- Em caso de falha, a excecao sobe para o runtime do Lambda.
- O SQS torna a mensagem visivel novamente apos o visibility_timeout (1 hora).
- Apos 3 tentativas, a mensagem vai para a DLQ.
- NAO fazer try/except silencioso - deixar o Lambda falhar para o SQS retentar.

TODO: substituir o log em _efetivar_cancelamento pela chamada real a API externa.
"""

import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

API_CANCELAMENTO_URL = os.environ.get("API_CANCELAMENTO_URL", "")


def lambda_handler(event, context):
    records = event.get("Records", [])
    logger.info("Iniciando efetivacao de cancelamentos. total_mensagens=%d", len(records))

    for record in records:
        _processar_registro(record)

    logger.info("Efetivacao finalizada com sucesso.")
    return {"statusCode": 200}


def _processar_registro(record):
    body = json.loads(record["body"])
    logger.info("Mensagem recebida para efetivacao: %s", json.dumps(body))

    _validar_payload(body)

    id_boleto = body["id_boleto_individual"]
    data_baixa = body["data_baixa_automatica"]

    logger.info(
        "Iniciando efetivacao do cancelamento. id_boleto=%s data_baixa=%s",
        id_boleto, data_baixa,
    )

    _efetivar_cancelamento(id_boleto, data_baixa, body)

    logger.info("Cancelamento efetivado com sucesso. id_boleto=%s", id_boleto)


def _efetivar_cancelamento(id_boleto, data_baixa, payload):
    """
    TODO: implementar chamada real a API externa quando disponivel.
    Por enquanto apenas loga o payload recebido.
    """
    logger.info(
        "[TODO] Chamada a API externa de cancelamento. "
        "id_boleto=%s data_baixa=%s api_url=%s payload=%s",
        id_boleto,
        data_baixa,
        API_CANCELAMENTO_URL or "(nao configurada)",
        json.dumps(payload),
    )

    # Exemplo de implementacao futura com urllib:
    #
    # import urllib.request
    # import urllib.error
    #
    # request_body = json.dumps({
    #     "id_boleto_individual": id_boleto,
    #     "data_baixa_automatica": data_baixa,
    # }).encode("utf-8")
    #
    # req = urllib.request.Request(
    #     url=f"{API_CANCELAMENTO_URL}/{id_boleto}/cancelar",
    #     data=request_body,
    #     headers={"Content-Type": "application/json"},
    #     method="POST",
    # )
    #
    # try:
    #     with urllib.request.urlopen(req, timeout=30) as response:
    #         logger.info("API respondeu. status=%d id_boleto=%s", response.status, id_boleto)
    # except urllib.error.HTTPError as e:
    #     logger.error("Erro HTTP na API. status=%d id_boleto=%s", e.code, id_boleto)
    #     raise
    # except urllib.error.URLError as e:
    #     logger.error("Erro de conexao com a API. id_boleto=%s error=%s", id_boleto, e)
    #     raise


def _validar_payload(body):
    campos_obrigatorios = ["id_boleto_individual", "data_baixa_automatica"]
    ausentes = [c for c in campos_obrigatorios if not body.get(c)]
    if ausentes:
        raise ValueError(
            f"Payload invalido. Campos ausentes: {ausentes}. Body: {body}"
        )

