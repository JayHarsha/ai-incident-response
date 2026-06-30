package com.incidentplatform.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "incidents")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class IncidentEntity {

    // --- 1. Primary & Distributed Keys ---
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "incident_id", nullable = false, unique = true, updatable = false)
    private String incidentId;

    @Column(name = "trace_id", nullable = false, unique = true, updatable = false)
    private String traceId;

    // --- 2. Core Incident Metadata (Phase 1) ---
    @Column(name = "service_name", nullable = false)
    private String serviceName;

    @Column(name = "environment", nullable = false)
    private String environment;

    @Column(name = "severity", nullable = false)
    private String severity;

    @Column(name = "status", nullable = false)
    private String status;

    // --- 3. Technical Payload (Phase 1) ---
    @Column(name = "error_message", columnDefinition = "TEXT", nullable = false)
    private String errorMessage;

    @Column(name = "stack_trace", columnDefinition = "TEXT")
    private String stackTrace;

    @Column(name = "endpoint_or_operation")
    private String endpointOrOperation;

    // --- 4. AI & RAG Intelligence Engine (Phases 4 - 7) ---
    @Column(name = "matched_runbook")
    private String matchedRunbook;

    @Column(name = "root_cause_hypothesis", columnDefinition = "TEXT")
    private String rootCauseHypothesis;

    @Column(name = "remediation_steps", columnDefinition = "TEXT")
    private String remediationSteps;

    @Column(name = "impacted_services", columnDefinition = "TEXT")
    private String impactedServices;

    @Column(name = "similar_past_incidents", columnDefinition = "TEXT")
    private String similarPastIncidents;

    @Column(name = "ai_confidence_score")
    private Double aiConfidenceScore;

    @Column(name = "ai_analysis_timestamp")
    private LocalDateTime aiAnalysisTimestamp;

    // --- 5. Audit & Lifecycle ---
    @Column(name = "resolved_by")
    private String resolvedBy;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    // --- JPA Lifecycle Hooks ---
    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
        this.updatedAt = this.createdAt;

        if (this.traceId == null) {
            this.traceId = UUID.randomUUID().toString();
        }
        if (this.incidentId == null) {
            this.incidentId = "INC-" + (System.currentTimeMillis() % 100000);
        }
        if (this.status == null) {
            this.status = "OPEN";
        }
        if (this.environment == null) {
            this.environment = "PROD";
        }
    }

    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
}