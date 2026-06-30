package com.incidentplatform.service.impl;

import com.incidentplatform.entity.IncidentEntity;
import com.incidentplatform.repository.IncidentRepository;
import com.incidentplatform.service.IncidentService;
import com.incidentplatform.service.KafkaEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class IncidentServiceImpl implements IncidentService {

    private final IncidentRepository incidentRepository;
    private final KafkaEventPublisher eventPublisher;

    public IncidentServiceImpl(IncidentRepository incidentRepository, KafkaEventPublisher eventPublisher) {
        this.incidentRepository = incidentRepository;
        this.eventPublisher = eventPublisher;
    }

    @Override
    @Transactional
    public IncidentEntity createIncident(IncidentEntity incident) {
        IncidentEntity savedIncident = incidentRepository.save(incident);
        eventPublisher.publishIncidentCreatedEvent(savedIncident);
        return savedIncident;
    }

    @Override
    @Transactional(readOnly = true)
    public List<IncidentEntity> getAllIncidents() {
        return incidentRepository.findAllByOrderByCreatedAtDesc();
    }

    @Override
    @Transactional(readOnly = true)
    public IncidentEntity getIncidentByIncidentId(String incidentId) {
        return incidentRepository.findByIncidentId(incidentId)
                .orElseThrow(() -> new IllegalArgumentException("Incident not found: " + incidentId));
    }

    @Override
    @Transactional
    public IncidentEntity updateStatus(String incidentId, String status, String resolvedBy) {
        IncidentEntity incident = incidentRepository.findByIncidentId(incidentId)
                .orElseThrow(() -> new IllegalArgumentException("Incident not found: " + incidentId));
        incident.setStatus(status);
        if (resolvedBy != null) {
            incident.setResolvedBy(resolvedBy);
        }
        return incidentRepository.save(incident);
    }

    @Override
    @Transactional(readOnly = true)
    public List<IncidentEntity> getIncidentsByService(String serviceName) {
        return incidentRepository.findByServiceNameOrderByCreatedAtDesc(serviceName);
    }
}
