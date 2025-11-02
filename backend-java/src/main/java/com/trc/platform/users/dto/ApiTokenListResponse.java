package com.trc.platform.users.dto;

import java.time.LocalDateTime;
import java.util.UUID;
import lombok.Builder;

@Builder
public record ApiTokenListResponse(
        UUID id,
        String name,
        LocalDateTime createdAt,
        LocalDateTime lastUsedAt,
        LocalDateTime expiresAt,
        LocalDateTime revokedAt,
        String tokenPrefix) {}
