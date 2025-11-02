package com.trc.platform.admin.dto;

import java.time.LocalDateTime;
import java.util.UUID;
import lombok.Builder;

@Builder
public record InviteCodeResponse(
        UUID id,
        String code,
        Boolean active,
        LocalDateTime createdAt,
        LocalDateTime expiresAt,
        LocalDateTime usedAt,
        UUID usedByUserId,
        UUID createdByUserId,
        String createdByUserEmail) {}
