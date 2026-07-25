package com.poc.agendamentobaixaboleto.domain.port;

import com.poc.agendamentobaixaboleto.domain.model.AgendamentoCancelamentoBoleto;

/**
 * Port de saída (output port) do domínio.
 * Define o contrato para publicação de um agendamento de cancelamento de boleto
 * em um sistema de mensageria, sem que o domínio conheça os detalhes da implementação.
 */
public interface AgendamentoCancelamentoBoletoPublisherPort {

    /**
     * Publica o agendamento de cancelamento do boleto na fila de processamento.
     *
     * @param agendamento o aggregate root com os dados do agendamento a ser publicado
     */
    void publicarAgendamento(AgendamentoCancelamentoBoleto agendamento);
}

