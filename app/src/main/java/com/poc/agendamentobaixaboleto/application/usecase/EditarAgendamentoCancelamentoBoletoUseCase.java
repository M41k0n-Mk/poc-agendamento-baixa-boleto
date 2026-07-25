package com.poc.agendamentobaixaboleto.application.usecase;

import com.poc.agendamentobaixaboleto.domain.model.AgendamentoCancelamentoBoleto;
import com.poc.agendamentobaixaboleto.domain.port.AgendamentoCancelamentoBoletoPublisherPort;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.UUID;

/**
 * Use case responsável por editar a data de cancelamento de um boleto já agendado.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class EditarAgendamentoCancelamentoBoletoUseCase {

    private final AgendamentoCancelamentoBoletoPublisherPort publisherPort;

    public void executar(UUID idBoletoIndividual, LocalDate novaDataBaixaAutomatica) {
        log.info("Iniciando edição de agendamento de cancelamento. idBoletoIndividual={}, novaData={}",
                idBoletoIndividual, novaDataBaixaAutomatica);

        AgendamentoCancelamentoBoleto agendamento =
                AgendamentoCancelamentoBoleto.criarEdicaoDeDataCancelamento(idBoletoIndividual, novaDataBaixaAutomatica);

        publisherPort.publicarAgendamento(agendamento);

        log.info("Edição de agendamento publicada com sucesso. idBoletoIndividual={}, tipo={}",
                idBoletoIndividual, agendamento.getTipo());
    }
}

