package com.poc.agendamentobaixaboleto.infrastructure.web.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Future;
import jakarta.validation.constraints.NotNull;

import java.time.LocalDate;
import java.util.UUID;

/**
 * DTO de entrada para criação de um agendamento de cancelamento de boleto.
 */
public record CriarAgendamentoRequest(

        @NotNull(message = "O campo id_boleto_individual é obrigatório.")
        @JsonProperty("id_boleto_individual")
        UUID idBoletoIndividual,

        @NotNull(message = "O campo data_baixa_automatica é obrigatório.")
        @Future(message = "A data de baixa automática deve ser uma data futura.")
        @JsonProperty("data_baixa_automatica")
        LocalDate dataBaixaAutomatica
) {}

