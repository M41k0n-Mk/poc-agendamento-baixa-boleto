package com.poc.agendamentobaixaboleto.infrastructure.messaging;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.poc.agendamentobaixaboleto.domain.exception.PublicacaoAgendamentoNaFilaException;
import com.poc.agendamentobaixaboleto.domain.model.AgendamentoCancelamentoBoleto;
import com.poc.agendamentobaixaboleto.domain.port.AgendamentoCancelamentoBoletoPublisherPort;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import software.amazon.awssdk.services.sqs.SqsAsyncClient;
import software.amazon.awssdk.services.sqs.model.SendMessageRequest;

import java.util.Map;

/**
 * Adapter de saída: publica mensagens no SQS usando SqsAsyncClient diretamente.
 * Usa a URL completa da fila para evitar problemas de resolução de nome pelo Spring Cloud AWS.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AgendamentoCancelamentoBoletoSqsPublisher implements AgendamentoCancelamentoBoletoPublisherPort {

    private final SqsAsyncClient sqsAsyncClient;
    private final ObjectMapper objectMapper;

    @Value("${app.sqs.agendamento-cancelamento-queue-url}")
    private String queueUrl;

    @Override
    public void publicarAgendamento(AgendamentoCancelamentoBoleto agendamento) {
        try {
            Map<String, Object> payload = Map.of(
                    "data_baixa_automatica", agendamento.getDataBaixaAutomatica().toString(),
                    "tipo", agendamento.getTipo().name(),
                    "id_boleto_individual", agendamento.getIdBoletoIndividual().toString()
            );

            String mensagem = objectMapper.writeValueAsString(payload);

            log.info("Publicando mensagem na fila. tipo={}, idBoleto={}",
                    agendamento.getTipo(), agendamento.getIdBoletoIndividual());

            sqsAsyncClient.sendMessage(SendMessageRequest.builder()
                    .queueUrl(queueUrl)
                    .messageBody(mensagem)
                    .build())
                    .join(); // bloqueia até confirmar o envio

            log.info("Mensagem publicada com sucesso na fila de agendamento.");
        } catch (Exception e) {
            log.error("Erro ao publicar mensagem na fila SQS.", e);
            throw new PublicacaoAgendamentoNaFilaException(
                    "Falha ao publicar agendamento na fila: " + e.getMessage(), e);
        }
    }
}

