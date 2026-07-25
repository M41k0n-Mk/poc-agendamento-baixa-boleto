package com.poc.agendamentobaixaboleto.domain.exception;

/**
 * Exceção base do domínio de agendamento de cancelamento de boleto.
 * Todas as exceções de negócio devem estender esta classe.
 */
public abstract class AgendamentoCancelamentoDomainException extends RuntimeException {

    protected AgendamentoCancelamentoDomainException(String mensagem) {
        super(mensagem);
    }

    protected AgendamentoCancelamentoDomainException(String mensagem, Throwable causa) {
        super(mensagem, causa);
    }
}

