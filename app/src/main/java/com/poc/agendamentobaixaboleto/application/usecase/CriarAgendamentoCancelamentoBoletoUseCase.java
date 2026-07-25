package com.poc.agendamentobaixaboleto.application.usecase;

import com.poc.agendamentobaixaboleto.domain.model.AgendamentoCancelamentoBoleto;
import com.poc.agendamentobaixaboleto.domain.port.AgendamentoCancelamentoBoletoPublisherPort;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.UUID;

/**
 * Use case responsável por criar um novo agendamento de cancelamento de boleto.
 * Orquestra a criação do aggregate e a publicação na fila de processamento.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CriarAgendamentoCancelamentoBoletoUseCase {

    private final AgendamentoCancelamentoBoletoPublisherPort publisherPort;

    /**
     * Cria e publica um novo agendamento de cancelamento para o boleto informado.
     *
     * @param idBoletoIndividual identificador único do boleto a ser cancelado
     * @param dataBaixaAutomatica data em que o cancelamento deve ser efetivado
     */
    public void executar(UUID idBoletoIndividual, LocalDate dataBaixaAutomatica) {
        log.info("Iniciando criação de agendamento de cancelamento. idBoletoIndividual={}, dataBaixaAutomatica={}",
                idBoletoIndividual, dataBaixaAutomatica);

        AgendamentoCancelamentoBoleto agendamento =
                AgendamentoCancelamentoBoleto.criarNovoAgendamento(idBoletoIndividual, dataBaixaAutomatica);

        publisherPort.publicarAgendamento(agendamento);

        log.info("Agendamento de cancelamento criado e publicado com sucesso. idBoletoIndividual={}, tipo={}",
                idBoletoIndividual, agendamento.getTipo());
    }
}

