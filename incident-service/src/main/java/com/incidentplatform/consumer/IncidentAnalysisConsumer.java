package com.incidentplatform.consumer;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.incidentplatform.dto.AnalysisResultDto;
import com.incidentplatform.repository.IncidentRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Component
@Slf4j
public class IncidentAnalysisConsumer {

    private final IncidentRepository incidentRepository;
    private final ObjectMapper objectMapper;

    public IncidentAnalysisConsumer(IncidentRepository incidentRepository, ObjectMapper objectMapper) {
        this.incidentRepository = incidentRepository;
        this.objectMapper = objectMapper;
    }

    @KafkaListener(topics = "incident-analyzed", groupId = "incident-service-group",
            containerFactory = "kafkaListenerContainerFactory")
    @Transactional
    public void consumeAnalysisResult(String message) {
        log.info("Received analysis result from Kafka: {}", message.substring(0, Math.min(100, message.length())));
        try {
            AnalysisResultDto result = objectMapper.readValue(message, AnalysisResultDto.class);

            incidentRepository.findByIncidentId(result.getIncidentId()).ifPresentOrElse(incident -> {
                incident.setRootCauseHypothesis(result.getRootCause());
                incident.setRemediationSteps(joinList(result.getRecommendedSteps()));
                incident.setImpactedServices(joinList(result.getImpactedServices()));
                incident.setSimilarPastIncidents(joinList(result.getSimilarPastIncidents()));
                incident.setMatchedRunbook(result.getMatchedRunbook());
                incident.setAiConfidenceScore(result.getConfidenceScore());
                incident.setStatus("ANALYZED");
                incident.setAiAnalysisTimestamp(LocalDateTime.now());
                incidentRepository.save(incident);
                log.info("Updated incident {} with AI analysis (confidence: {})",
                        result.getIncidentId(), result.getConfidenceScore());
            }, () -> log.warn("Received analysis for unknown incident ID: {}", result.getIncidentId()));

        } catch (Exception e) {
            log.error("Failed to process analysis result from Kafka", e);
        }
    }

    private String joinList(List<String> items) {
        if (items == null || items.isEmpty()) return "";
        return String.join("\n", items.stream().map(s -> "• " + s).toList());
    }
}
