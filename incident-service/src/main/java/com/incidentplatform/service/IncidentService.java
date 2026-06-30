package com.incidentplatform.service;

import com.incidentplatform.entity.IncidentEntity;

import java.util.List;

public interface IncidentService {
    IncidentEntity createIncident(IncidentEntity incident);
    List<IncidentEntity> getAllIncidents();
    IncidentEntity getIncidentByIncidentId(String incidentId);
    IncidentEntity updateStatus(String incidentId, String status, String resolvedBy);
    List<IncidentEntity> getIncidentsByService(String serviceName);
}
