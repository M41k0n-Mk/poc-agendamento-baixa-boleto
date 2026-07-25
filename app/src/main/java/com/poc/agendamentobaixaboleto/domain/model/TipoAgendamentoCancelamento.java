package com.poc.agendamentobaixaboleto.domain.model;

/**
 * Representa os tipos de operação possíveis para um agendamento de cancelamento de boleto.
 * AGENDAR_CANCELAMENTO: cria um novo agendamento de baixa para o boleto informado.
 * EDITAR_DATA_CANCELAMENTO: atualiza a data de baixa de um agendamento já existente.
 */
public enum TipoAgendamentoCancelamento {
    AGENDAR_CANCELAMENTO,
    EDITAR_DATA_CANCELAMENTO
}

