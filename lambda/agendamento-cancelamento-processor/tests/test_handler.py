"""
Testes unitários do Lambda agendamento-cancelamento-processor.
Execute com: python -m pytest tests/ -v
"""

import json
import os
import unittest
from unittest.mock import patch

from botocore.exceptions import ClientError

# Seta as variáveis de ambiente antes de importar o handler
os.environ["EFETIVAR_CANCELAMENTO_QUEUE_ARN"] = "arn:aws:sqs:sa-east-1:123456789012:test-efetivar-cancelamento"
os.environ["SCHEDULER_ROLE_ARN"] = "arn:aws:iam::123456789012:role/test-scheduler-role"
os.environ["SCHEDULE_GROUP_NAME"] = "cancelamento-boletos-test"

import handler  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_sqs_event(payload: dict) -> dict:
    return {"Records": [{"messageId": "test-id", "body": json.dumps(payload)}]}


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Operation")


PAYLOAD_AGENDAR = {
    "id_boleto_individual": "550e8400-e29b-41d4-a716-446655440000",
    "data_baixa_automatica": "2027-08-10",
    "tipo": "AGENDAR_CANCELAMENTO",
}

PAYLOAD_EDITAR = {
    "id_boleto_individual": "550e8400-e29b-41d4-a716-446655440000",
    "data_baixa_automatica": "2027-09-15",
    "tipo": "EDITAR_DATA_CANCELAMENTO",
}

EXPECTED_SCHEDULE_NAME = "cancelamento-550e8400-e29b-41d4-a716-446655440000"


# ---------------------------------------------------------------------------
# Testes — fluxo principal
# ---------------------------------------------------------------------------
class TestAgendamentoCancelamentoHandler(unittest.TestCase):

    @patch.object(handler, "scheduler_client")
    def test_agendar_cancelamento_chama_create_schedule(self, mock_scheduler):
        """AGENDAR_CANCELAMENTO deve chamar create_schedule com os parâmetros corretos."""
        mock_scheduler.create_schedule.return_value = {}

        handler.lambda_handler(_make_sqs_event(PAYLOAD_AGENDAR), None)

        mock_scheduler.create_schedule.assert_called_once()
        kwargs = mock_scheduler.create_schedule.call_args[1]

        self.assertEqual(kwargs["Name"], EXPECTED_SCHEDULE_NAME)
        self.assertEqual(kwargs["ScheduleExpression"], "at(2027-08-10T03:00:00)")
        self.assertEqual(kwargs["GroupName"], "cancelamento-boletos-test")
        self.assertEqual(kwargs["ActionAfterCompletion"], "DELETE")
        self.assertEqual(kwargs["Target"]["Arn"], os.environ["EFETIVAR_CANCELAMENTO_QUEUE_ARN"])
        self.assertEqual(kwargs["Target"]["RoleArn"], os.environ["SCHEDULER_ROLE_ARN"])

    @patch.object(handler, "scheduler_client")
    def test_editar_cancelamento_chama_update_schedule(self, mock_scheduler):
        """EDITAR_DATA_CANCELAMENTO deve chamar update_schedule com a nova data."""
        mock_scheduler.update_schedule.return_value = {}

        handler.lambda_handler(_make_sqs_event(PAYLOAD_EDITAR), None)

        mock_scheduler.update_schedule.assert_called_once()
        kwargs = mock_scheduler.update_schedule.call_args[1]
        self.assertEqual(kwargs["ScheduleExpression"], "at(2027-09-15T03:00:00)")
        self.assertEqual(kwargs["Name"], EXPECTED_SCHEDULE_NAME)

    @patch.object(handler, "scheduler_client")
    def test_input_do_target_contem_payload_original(self, mock_scheduler):
        """O campo Target.Input deve conter o payload original para a fila efetivar."""
        mock_scheduler.create_schedule.return_value = {}

        handler.lambda_handler(_make_sqs_event(PAYLOAD_AGENDAR), None)

        kwargs = mock_scheduler.create_schedule.call_args[1]
        target_input = json.loads(kwargs["Target"]["Input"])
        self.assertEqual(target_input["id_boleto_individual"], PAYLOAD_AGENDAR["id_boleto_individual"])
        self.assertEqual(target_input["data_baixa_automatica"], PAYLOAD_AGENDAR["data_baixa_automatica"])


# ---------------------------------------------------------------------------
# Testes — idempotência
# ---------------------------------------------------------------------------
class TestIdempotencia(unittest.TestCase):

    @patch.object(handler, "scheduler_client")
    def test_agendar_com_schedule_existente_faz_update(self, mock_scheduler):
        """ConflictException no create → deve fazer update (idempotência de reprocessamento)."""
        mock_scheduler.create_schedule.side_effect = _client_error("ConflictException")
        mock_scheduler.update_schedule.return_value = {}

        handler.lambda_handler(_make_sqs_event(PAYLOAD_AGENDAR), None)

        mock_scheduler.update_schedule.assert_called_once()

    @patch.object(handler, "scheduler_client")
    def test_editar_sem_schedule_existente_faz_create(self, mock_scheduler):
        """ResourceNotFoundException no update → deve fazer create (schedule ainda não existe)."""
        mock_scheduler.update_schedule.side_effect = _client_error("ResourceNotFoundException")
        mock_scheduler.create_schedule.return_value = {}

        handler.lambda_handler(_make_sqs_event(PAYLOAD_EDITAR), None)

        mock_scheduler.create_schedule.assert_called_once()


# ---------------------------------------------------------------------------
# Testes — erros e validações
# ---------------------------------------------------------------------------
class TestErros(unittest.TestCase):

    def test_tipo_desconhecido_lanca_value_error(self):
        """Tipo desconhecido deve ir direto para a DLQ via ValueError."""
        payload = {**PAYLOAD_AGENDAR, "tipo": "TIPO_INVALIDO"}
        with self.assertRaises(ValueError) as ctx:
            handler.lambda_handler(_make_sqs_event(payload), None)
        self.assertIn("TIPO_INVALIDO", str(ctx.exception))

    def test_payload_sem_tipo_lanca_value_error(self):
        payload = {"id_boleto_individual": "abc", "data_baixa_automatica": "2027-01-01"}
        with self.assertRaises(ValueError):
            handler.lambda_handler(_make_sqs_event(payload), None)

    def test_payload_sem_id_boleto_lanca_value_error(self):
        payload = {"tipo": "AGENDAR_CANCELAMENTO", "data_baixa_automatica": "2027-01-01"}
        with self.assertRaises(ValueError):
            handler.lambda_handler(_make_sqs_event(payload), None)

    def test_payload_sem_data_baixa_lanca_value_error(self):
        payload = {"tipo": "AGENDAR_CANCELAMENTO", "id_boleto_individual": "abc"}
        with self.assertRaises(ValueError):
            handler.lambda_handler(_make_sqs_event(payload), None)

    @patch.object(handler, "scheduler_client")
    def test_erro_inesperado_no_scheduler_relanca_excecao(self, mock_scheduler):
        """Erro não tratado deve propagar para o SQS reprocessar a mensagem."""
        mock_scheduler.create_schedule.side_effect = _client_error("ServiceUnavailableException")
        with self.assertRaises(ClientError):
            handler.lambda_handler(_make_sqs_event(PAYLOAD_AGENDAR), None)

    @patch.object(handler, "scheduler_client")
    def test_multiplos_registros_processados(self, mock_scheduler):
        """Múltiplos records no evento devem ser todos processados."""
        mock_scheduler.create_schedule.return_value = {}
        mock_scheduler.update_schedule.return_value = {}

        event = {
            "Records": [
                {"messageId": "1", "body": json.dumps(PAYLOAD_AGENDAR)},
                {"messageId": "2", "body": json.dumps(PAYLOAD_EDITAR)},
            ]
        }
        handler.lambda_handler(event, None)

        mock_scheduler.create_schedule.assert_called_once()
        mock_scheduler.update_schedule.assert_called_once()


if __name__ == "__main__":
    unittest.main()

Execute com: python -m pytest tests/ -v
"""

import json
import os
import unittest
from unittest.mock import MagicMock, patch, call

# Seta as variáveis de ambiente antes de importar o handler
os.environ["EFETIVAR_CANCELAMENTO_QUEUE_ARN"] = "arn:aws:sqs:sa-east-1:123456789012:test-efetivar-cancelamento"
os.environ["SCHEDULER_ROLE_ARN"] = "arn:aws:iam::123456789012:role/test-scheduler-role"
os.environ["SCHEDULE_GROUP_NAME"] = "cancelamento-boletos-test"

import handler  # noqa: E402  (importado após setar env vars)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_sqs_event(payload: dict) -> dict:
    return {
        "Records": [
            {
                "messageId": "test-message-id",
                "body": json.dumps(payload),
            }
        ]
    }


PAYLOAD_AGENDAR = {
    "id_boleto_individual": "550e8400-e29b-41d4-a716-446655440000",
    "data_baixa_automatica": "2027-08-10",
    "tipo": "AGENDAR_CANCELAMENTO",
}

PAYLOAD_EDITAR = {
    "id_boleto_individual": "550e8400-e29b-41d4-a716-446655440000",
    "data_baixa_automatica": "2027-09-15",
    "tipo": "EDITAR_DATA_CANCELAMENTO",
}


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------
class TestLambdaHandler(unittest.TestCase):

    @patch.object(handler, "scheduler_client")
    def test_agendar_cancelamento_cria_schedule(self, mock_scheduler):
        """AGENDAR_CANCELAMENTO deve chamar create_schedule."""
        mock_scheduler.create_schedule.return_value = {}

        handler.lambda_handler(_make_sqs_event(PAYLOAD_AGENDAR), None)

        mock_scheduler.create_schedule.assert_called_once()
        args = mock_scheduler.create_schedule.call_args[1]
        self.assertEqual(args["Name"], "cancelamento-550e8400-e29b-41d4-a716-446655440000")
        self.assertIn("at(2027-08-10T03:00:00)", args["ScheduleExpression"])
        self.assertEqual(args["ActionAfterCompletion"], "DELETE")
        self.assertEqual(args["Target"]["Arn"], os.environ["EFETIVAR_CANCELAMENTO_QUEUE_ARN"])

    @patch.object(handler, "scheduler_client")
    def test_editar_cancelamento_atualiza_schedule(self, mock_scheduler):
        """EDITAR_DATA_CANCELAMENTO deve chamar update_schedule."""
        mock_scheduler.update_schedule.return_value = {}

        handler.lambda_handler(_make_sqs_event(PAYLOAD_EDITAR), None)

        mock_scheduler.update_schedule.assert_called_once()
        args = mock_scheduler.update_schedule.call_args[1]
        self.assertIn("at(2027-09-15T03:00:00)", args["ScheduleExpression"])

    @patch.object(handler, "scheduler_client")
    def test_agendar_idempotente_quando_schedule_ja_existe(self, mock_scheduler):
        """Se schedule já existe (ConflictException), deve chamar update_schedule."""
        from botocore.exceptions import ClientError

        mock_scheduler.create_schedule.side_effect = ClientError(
            {"Error": {"Code": "ConflictException", "Message": "already exists"}},
            "CreateSchedule",
        )
        mock_scheduler.update_schedule.return_value = {}

        handler.lambda_handler(_make_sqs_event(PAYLOAD_AGENDAR), None)

        mock_scheduler.update_schedule.assert_called_once()

    @patch.object(handler, "scheduler_client")
    def test_editar_idempotente_quando_schedule_nao_existe(self, mock_scheduler):
        """Se schedule não existe (ResourceNotFoundException), deve chamar create_schedule."""
        from botocore.exceptions import ClientError

        mock_scheduler.update_schedule.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "not found"}},
            "UpdateSchedule",
        )
        mock_scheduler.create_schedule.return_value = {}

        handler.lambda_handler(_make_sqs_event(PAYLOAD_EDITAR), None)

        mock_scheduler.create_schedule.assert_called_once()

    def test_tipo_desconhecido_lanca_excecao(self):
        """Tipo desconhecido deve lançar ValueError para ir à DLQ."""
        payload = {**PAYLOAD_AGENDAR, "tipo": "TIPO_INVALIDO"}

        with self.assertRaises(ValueError) as ctx:
            handler.lambda_handler(_make_sqs_event(payload), None)

        self.assertIn("TIPO_INVALIDO", str(ctx.exception))

    def test_payload_incompleto_lanca_excecao(self):
        """Payload sem campos obrigatórios deve lançar ValueError para ir à DLQ."""
        payload = {"tipo": "AGENDAR_CANCELAMENTO"}  # faltam campos

        with self.assertRaises(ValueError) as ctx:
            handler.lambda_handler(_make_sqs_event(payload), None)

        self.assertIn("ausentes", str(ctx.exception))

    @patch.object(handler, "scheduler_client")
    def test_multiplos_registros_processados(self, mock_scheduler):
        """Múltiplos records no evento devem ser todos processados."""
        mock_scheduler.create_schedule.return_value = {}
        mock_scheduler.update_schedule.return_value = {}

        event = {
            "Records": [
                {"messageId": "1", "body": json.dumps(PAYLOAD_AGENDAR)},
                {"messageId": "2", "body": json.dumps(PAYLOAD_EDITAR)},
            ]
        }

        handler.lambda_handler(event, None)

        mock_scheduler.create_schedule.assert_called_once()
        mock_scheduler.update_schedule.assert_called_once()


if __name__ == "__main__":
    unittest.main()

