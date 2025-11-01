package com.trc.platform.core.dto;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import lombok.Builder;

@Builder
public record SolveResponse(
        String requestId, String result, Integer durationMs, Map<String, Integer> timings) {

    // Compact constructor to handle defensive copying of timings map
    public SolveResponse {
        timings = timings == null ? null : new HashMap<>(timings);
    }

    @Override
    public Map<String, Integer> timings() {
        return timings == null ? null : Collections.unmodifiableMap(timings);
    }
}
