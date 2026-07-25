package com.poc.agendamentobaixaboleto.infrastructure.web.handler;

import com.poc.agendamentobaixaboleto.domain.exception.DataBaixaAutomaticaInvalidaException;
import com.poc.agendamentobaixaboleto.domain.exception.PublicacaoAgendamentoNaFilaException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.net.URI;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Handler global de exceções — retorna respostas no formato RFC 7807 (Problem Details).
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail handleValidation(MethodArgumentNotValidException ex) {
        Map<String, String> erros = ex.getBindingResult().getFieldErrors().stream()
                .collect(Collectors.toMap(
                        FieldError::getField,
                        fe -> fe.getDefaultMessage() != null ? fe.getDefaultMessage() : "inválido",
                        (a, b) -> a
                ));

        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.UNPROCESSABLE_ENTITY);
        problem.setType(URI.create("urn:problema:validacao"));
        problem.setTitle("Erro de validação");
        problem.setDetail("Um ou mais campos estão inválidos.");
        problem.setProperty("campos", erros);
        return problem;
    }

    @ExceptionHandler(DataBaixaAutomaticaInvalidaException.class)
    public ProblemDetail handleDataInvalida(DataBaixaAutomaticaInvalidaException ex) {
        log.warn("Data de baixa inválida: {}", ex.getMessage());
        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.UNPROCESSABLE_ENTITY);
        problem.setType(URI.create("urn:problema:data-invalida"));
        problem.setTitle("Data de baixa inválida");
        problem.setDetail(ex.getMessage());
        return problem;
    }

    @ExceptionHandler(PublicacaoAgendamentoNaFilaException.class)
    public ProblemDetail handlePublicacaoFila(PublicacaoAgendamentoNaFilaException ex) {
        log.error("Falha ao publicar na fila SQS.", ex);
        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.BAD_GATEWAY);
        problem.setType(URI.create("urn:problema:fila-indisponivel"));
        problem.setTitle("Fila indisponível");
        problem.setDetail("Não foi possível enfileirar o agendamento no momento. Tente novamente.");
        return problem;
    }

    @ExceptionHandler(Exception.class)
    public ProblemDetail handleGenerico(Exception ex) {
        log.error("Erro inesperado.", ex);
        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.INTERNAL_SERVER_ERROR);
        problem.setType(URI.create("urn:problema:erro-interno"));
        problem.setTitle("Erro interno");
        problem.setDetail("Ocorreu um erro inesperado. Tente novamente mais tarde.");
        return problem;
    }
}

