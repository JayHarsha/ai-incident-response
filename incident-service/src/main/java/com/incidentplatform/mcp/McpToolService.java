package com.incidentplatform.mcp;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.incidentplatform.entity.IncidentEntity;
import com.incidentplatform.repository.IncidentRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;

@Service
@Slf4j
public class McpToolService {

    private final IncidentRepository incidentRepository;
    private final ObjectMapper objectMapper;

    public McpToolService(IncidentRepository incidentRepository, ObjectMapper objectMapper) {
        this.incidentRepository = incidentRepository;
        this.objectMapper = objectMapper;
    }

    /** Tool schemas returned by tools/list — the MCP client uses these for discovery. */
    public List<Map<String, Object>> definitions() {
        return List.of(
                Map.of(
                        "name", "update_incident_status",
                        "description", "Update the lifecycle status of an incident in the database",
                        "inputSchema", Map.of(
                                "type", "object",
                                "properties", Map.of(
                                        "incident_id", Map.of("type", "string",
                                                "description", "The incident ID (e.g. INC-12345)"),
                                        "status", Map.of("type", "string",
                                                "description", "New status: OPEN | ANALYZING | ANALYZED | RESOLVED")
                                ),
                                "required", List.of("incident_id", "status")
                        )
                ),
                Map.of(
                        "name", "get_incident",
                        "description", "Fetch full incident details from the database by ID",
                        "inputSchema", Map.of(
                                "type", "object",
                                "properties", Map.of(
                                        "incident_id", Map.of("type", "string",
                                                "description", "The incident ID to look up")
                                ),
                                "required", List.of("incident_id")
                        )
                )
        );
    }

    @Transactional
    public String execute(String toolName, Map<String, Object> args) throws JsonProcessingException {
        return switch (toolName) {
            case "update_incident_status" -> {
                String incidentId = (String) args.get("incident_id");
                String status = (String) args.get("status");
                incidentRepository.findByIncidentId(incidentId).ifPresentOrElse(
                        incident -> {
                            incident.setStatus(status);
                            incidentRepository.save(incident);
                            log.info("MCP: {} → {}", incidentId, status);
                        },
                        () -> log.warn("MCP: incident {} not found", incidentId)
                );
                yield "Status updated to " + status;
            }
            case "get_incident" -> {
                String incidentId = (String) args.get("incident_id");
                IncidentEntity incident = incidentRepository.findByIncidentId(incidentId)
                        .orElseThrow(() -> new IllegalArgumentException("Incident not found: " + incidentId));
                yield objectMapper.writeValueAsString(incident);
            }
            default -> throw new IllegalArgumentException("Unknown MCP tool: " + toolName);
        };
    }
}
