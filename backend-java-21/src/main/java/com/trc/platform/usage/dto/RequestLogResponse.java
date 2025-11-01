package com.trc.platform.usage.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.trc.platform.usage.entity.RequestLog;
import java.time.LocalDateTime;
import java.util.UUID;
import lombok.Builder;
import lombok.extern.jackson.Jacksonized;

@Jacksonized
@Builder
public record RequestLogResponse(
        UUID id,
        @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss") LocalDateTime requestTs,
        String service,
        RequestLog.RequestStatus status,
        Integer durationMs,
        Integer requestBytes,
        Integer responseBytes,
        UUID requestId,
        String flowId,
        String tokenPrefix) {}
