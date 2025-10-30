package com.trc.platform.users.dto;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;
import lombok.Builder;

@Builder
public record ApiTokenResponse(
        UUID id,
        Optional<String> token,
        String name,
        LocalDateTime createdAt,
        LocalDateTime lastUsedAt,
        LocalDateTime expiresAt,
        LocalDateTime revokedAt,
        String tokenPrefix) {}
