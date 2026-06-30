package com.incidentplatform.controller;

import com.incidentplatform.dto.StatusUpdateRequest;
import com.incidentplatform.entity.IncidentEntity;
import com.incidentplatform.service.IncidentService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/incidents")
public class IncidentController {

    private final IncidentService incidentService;

    public IncidentController(IncidentService incidentService) {
        this.incidentService = incidentService;
    }

    @PostMapping
    public ResponseEntity<IncidentEntity> createIncident(@RequestBody IncidentEntity incident) {
        return new ResponseEntity<>(incidentService.createIncident(incident), HttpStatus.CREATED);
    }

    @GetMapping
    public ResponseEntity<List<IncidentEntity>> getAllIncidents() {
        return ResponseEntity.ok(incidentService.getAllIncidents());
    }

    @GetMapping("/{incidentId}")
    public ResponseEntity<IncidentEntity> getIncidentById(@PathVariable String incidentId) {
        return ResponseEntity.ok(incidentService.getIncidentByIncidentId(incidentId));
    }

    @PutMapping("/{incidentId}/status")
    public ResponseEntity<IncidentEntity> updateStatus(
            @PathVariable String incidentId,
            @RequestBody StatusUpdateRequest request) {
        return ResponseEntity.ok(incidentService.updateStatus(incidentId, request.getStatus(), request.getResolvedBy()));
    }

    @GetMapping("/service/{serviceName}")
    public ResponseEntity<List<IncidentEntity>> getByService(@PathVariable String serviceName) {
        return ResponseEntity.ok(incidentService.getIncidentsByService(serviceName));
    }
}
