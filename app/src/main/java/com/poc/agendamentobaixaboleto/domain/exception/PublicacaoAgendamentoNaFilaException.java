package com.poc.agendamentobaixaboleto.domain.exception;

/**
 * Lançada quando ocorre uma falha ao publicar o agendamento na fila SQS.
 */
public class PublicacaoAgendamentoNaFilaException extends AgendamentoCancelamentoDomainException {

    public PublicacaoAgendamentoNaFilaException(String mensagem) {
        super(mensagem);
    }

    public PublicacaoAgendamentoNaFilaException(String mensagem, Throwable causa) {
        super(mensagem, causa);
    }
}

