package com.poc.agendamentobaixaboleto.domain.exception;

/**
 * Lançada quando a data de baixa automática informada é inválida
 * (nula ou não é uma data futura).
 */
public class DataBaixaAutomaticaInvalidaException extends AgendamentoCancelamentoDomainException {

    public DataBaixaAutomaticaInvalidaException(String mensagem) {
        super(mensagem);
    }
}

