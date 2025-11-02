package com.trc.platform.monitoring.dto;

import java.util.Map;
import lombok.Builder;

@Builder
public record HealthResponse(String status, Map<String, Boolean> checks) {}
