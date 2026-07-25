package com.poc.agendamentobaixaboleto.domain.model;

import com.poc.agendamentobaixaboleto.domain.exception.DataBaixaAutomaticaInvalidaException;

import java.time.LocalDate;
import java.util.UUID;

/**
 * Aggregate root do domínio de agendamento de cancelamento de boleto.
 * Encapsula as regras de negócio relacionadas ao agendamento da baixa automática.
 */
public class AgendamentoCancelamentoBoleto {

    private final UUID idBoletoIndividual;
    private LocalDate dataBaixaAutomatica;
    private final TipoAgendamentoCancelamento tipo;

    private AgendamentoCancelamentoBoleto(UUID idBoletoIndividual,
                                          LocalDate dataBaixaAutomatica,
                                          TipoAgendamentoCancelamento tipo) {
        this.idBoletoIndividual = idBoletoIndividual;
        this.dataBaixaAutomatica = dataBaixaAutomatica;
        this.tipo = tipo;
    }

    /**
     * Cria um novo agendamento de cancelamento para o boleto informado.
     * A data de baixa deve ser uma data futura.
     */
    public static AgendamentoCancelamentoBoleto criarNovoAgendamento(UUID idBoletoIndividual,
                                                                      LocalDate dataBaixaAutomatica) {
        validarDataBaixaAutomaticaEhFutura(dataBaixaAutomatica);
        return new AgendamentoCancelamentoBoleto(
                idBoletoIndividual,
                dataBaixaAutomatica,
                TipoAgendamentoCancelamento.AGENDAR_CANCELAMENTO
        );
    }

    /**
     * Cria um agendamento de edição de data de cancelamento para um boleto já agendado.
     * A nova data de baixa deve ser uma data futura.
     */
    public static AgendamentoCancelamentoBoleto criarEdicaoDeDataCancelamento(UUID idBoletoIndividual,
                                                                               LocalDate novaDataBaixaAutomatica) {
        validarDataBaixaAutomaticaEhFutura(novaDataBaixaAutomatica);
        return new AgendamentoCancelamentoBoleto(
                idBoletoIndividual,
                novaDataBaixaAutomatica,
                TipoAgendamentoCancelamento.EDITAR_DATA_CANCELAMENTO
        );
    }

    private static void validarDataBaixaAutomaticaEhFutura(LocalDate dataBaixaAutomatica) {
        if (dataBaixaAutomatica == null) {
            throw new DataBaixaAutomaticaInvalidaException("A data de baixa automática é obrigatória.");
        }
        if (!dataBaixaAutomatica.isAfter(LocalDate.now())) {
            throw new DataBaixaAutomaticaInvalidaException(
                    "A data de baixa automática deve ser uma data futura. Data informada: " + dataBaixaAutomatica
            );
        }
    }

    public UUID getIdBoletoIndividual() {
        return idBoletoIndividual;
    }

    public LocalDate getDataBaixaAutomatica() {
        return dataBaixaAutomatica;
    }

    public TipoAgendamentoCancelamento getTipo() {
        return tipo;
    }
}

