"""
Testes unitários do Lambda efetivar-cancelamento-processor.
Execute com: python -m pytest tests/ -v
"""

import json
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("API_CANCELAMENTO_URL", "https://api.example.com/v1/boletos")

import handler  # noqa: E402


def _make_sqs_event(payload: dict) -> dict:
    return {
        "Records": [
            {
                "messageId": "test-message-id",
                "body": json.dumps(payload),
            }
        ]
    }


PAYLOAD_VALIDO = {
    "id_boleto_individual": "550e8400-e29b-41d4-a716-446655440000",
    "data_baixa_automatica": "2027-08-10",
    "tipo": "AGENDAR_CANCELAMENTO",
}


class TestEfetivarCancelamentoHandler(unittest.TestCase):

    def test_mensagem_valida_processada_com_sucesso(self):
        """Mensagem válida deve ser processada sem lançar exceção."""
        result = handler.lambda_handler(_make_sqs_event(PAYLOAD_VALIDO), None)
        self.assertEqual(result["statusCode"], 200)

    def test_payload_sem_id_boleto_lanca_excecao(self):
        """Payload sem id_boleto_individual deve lançar ValueError → DLQ."""
        payload = {"data_baixa_automatica": "2027-08-10"}
        with self.assertRaises(ValueError) as ctx:
            handler.lambda_handler(_make_sqs_event(payload), None)
        self.assertIn("id_boleto_individual", str(ctx.exception))

    def test_payload_sem_data_baixa_lanca_excecao(self):
        """Payload sem data_baixa_automatica deve lançar ValueError → DLQ."""
        payload = {"id_boleto_individual": "550e8400-e29b-41d4-a716-446655440000"}
        with self.assertRaises(ValueError) as ctx:
            handler.lambda_handler(_make_sqs_event(payload), None)
        self.assertIn("data_baixa_automatica", str(ctx.exception))

    def test_multiplos_registros_processados(self):
        """Múltiplos records devem ser todos processados."""
        event = {
            "Records": [
                {"messageId": "1", "body": json.dumps(PAYLOAD_VALIDO)},
                {"messageId": "2", "body": json.dumps({
                    **PAYLOAD_VALIDO,
                    "id_boleto_individual": "660e8400-e29b-41d4-a716-446655440001",
                })},
            ]
        }
        result = handler.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 200)


if __name__ == "__main__":
    unittest.main()

