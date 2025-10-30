package com.trc.platform.monitoring.dto;

import java.util.Map;
import lombok.Builder;

@Builder
public record HealthResponse(
        /** Field description. */
        String status,

        /** Field description. */
        Map<String, Boolean> checks) {}
