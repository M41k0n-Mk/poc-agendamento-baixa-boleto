package com.poc.agendamentobaixaboleto.infrastructure.web.controller;

import com.poc.agendamentobaixaboleto.application.usecase.CriarAgendamentoCancelamentoBoletoUseCase;
import com.poc.agendamentobaixaboleto.application.usecase.EditarAgendamentoCancelamentoBoletoUseCase;
import com.poc.agendamentobaixaboleto.infrastructure.web.dto.AgendamentoResponse;
import com.poc.agendamentobaixaboleto.infrastructure.web.dto.CriarAgendamentoRequest;
import com.poc.agendamentobaixaboleto.infrastructure.web.dto.EditarAgendamentoRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * Controller REST para gerenciamento de agendamentos de cancelamento de boletos.
 *
 * POST /api/v1/agendamentos          → Cria um novo agendamento
 * PATCH /api/v1/agendamentos/{id}    → Edita a data de um agendamento existente
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/agendamentos")
@RequiredArgsConstructor
public class AgendamentoCancelamentoBoletoController {

    private final CriarAgendamentoCancelamentoBoletoUseCase criarUseCase;
    private final EditarAgendamentoCancelamentoBoletoUseCase editarUseCase;

    /**
     * Cria um novo agendamento de cancelamento para o boleto informado.
     */
    @PostMapping
    public ResponseEntity<AgendamentoResponse> criarAgendamento(
            @Valid @RequestBody CriarAgendamentoRequest request) {

        log.info("Recebida requisição para criar agendamento. idBoleto={}", request.idBoletoIndividual());

        criarUseCase.executar(request.idBoletoIndividual(), request.dataBaixaAutomatica());

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(AgendamentoResponse.of("Agendamento de cancelamento criado com sucesso."));
    }

    /**
     * Edita a data de cancelamento de um agendamento já existente.
     * O id do boleto é enviado no corpo por consistência com o payload do frontend.
     */
    @PatchMapping
    public ResponseEntity<AgendamentoResponse> editarAgendamento(
            @Valid @RequestBody EditarAgendamentoRequest request) {

        log.info("Recebida requisição para editar agendamento. idBoleto={}", request.idBoletoIndividual());

        editarUseCase.executar(request.idBoletoIndividual(), request.dataBaixaAutomatica());

        return ResponseEntity.ok(AgendamentoResponse.of("Data de cancelamento atualizada com sucesso."));
    }
}

