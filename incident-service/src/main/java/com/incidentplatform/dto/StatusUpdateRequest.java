package com.incidentplatform.dto;

import lombok.Data;

@Data
public class StatusUpdateRequest {
    private String status;
    private String resolvedBy;
}
