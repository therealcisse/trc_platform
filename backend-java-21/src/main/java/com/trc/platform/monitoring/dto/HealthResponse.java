package com.trc.platform.monitoring.dto;

import java.util.Map;

public record HealthResponse(
    /** Field description. */
    String status,

    /** Field description. */
    Map<String, Boolean> checks
) {}
