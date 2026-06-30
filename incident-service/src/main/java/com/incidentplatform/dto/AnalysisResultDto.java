package com.incidentplatform.dto;

import lombok.Data;

import java.util.List;

@Data
public class AnalysisResultDto {
    private String incidentId;
    private String rootCause;
    private List<String> impactedServices;
    private List<String> recommendedSteps;
    private List<String> similarPastIncidents;
    private Double confidenceScore;
    private String matchedRunbook;
    private String rawAnalysis;
}
