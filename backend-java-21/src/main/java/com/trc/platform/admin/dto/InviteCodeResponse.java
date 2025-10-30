package com.trc.platform.admin.dto;

import java.time.LocalDateTime;
import java.util.UUID;

public record InviteCodeResponse(
    /** Field description. */
    UUID id,

    /** Field description. */
    String code,

    /** Field description. */
    Boolean active,

    /** Field description. */
    LocalDateTime createdAt,

    /** Field description. */
    LocalDateTime expiresAt,

    /** Field description. */
    LocalDateTime usedAt,

    /** Field description. */
    UUID usedByUserId,

    /** Field description. */
    UUID createdByUserId,

    /** Field description. */
    String createdByUserEmail
) {}
