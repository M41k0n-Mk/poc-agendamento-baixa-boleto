package com.poc.agendamentobaixaboleto.infrastructure.web.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * DTO de resposta padrão da API.
 */
public record AgendamentoResponse(
        @JsonProperty("mensagem") String mensagem
) {
    public static AgendamentoResponse of(String mensagem) {
        return new AgendamentoResponse(mensagem);
    }
}

