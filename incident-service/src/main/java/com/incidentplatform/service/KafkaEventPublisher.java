package com.incidentplatform.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.incidentplatform.entity.IncidentEntity;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
@Slf4j
public class KafkaEventPublisher {

    private static final String TOPIC = "incident-created";

    // Accept Spring's default Object types
    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper;

    public KafkaEventPublisher(KafkaTemplate<String, String> kafkaTemplate, ObjectMapper objectMapper) {
        this.kafkaTemplate = kafkaTemplate;
        this.objectMapper = objectMapper;
    }

    public void publishIncidentCreatedEvent(IncidentEntity incident) {
        try {
            // Convert to JSON String
            String jsonPayload = objectMapper.writeValueAsString(incident);

            log.info("Publishing incident-created event to Kafka for ID: {}", incident.getIncidentId());

            // Send the String payload (which is valid as an Object)
            kafkaTemplate.send(TOPIC, incident.getIncidentId(), jsonPayload);

        } catch (JsonProcessingException e) {
            log.error("Failed to serialize IncidentEntity to JSON for Kafka", e);
        }
    }
}