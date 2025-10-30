package com.trc.platform.users.dto;

import jakarta.validation.constraints.NotBlank;

public record EmailVerificationRequest(
    @NotBlank(message = "Verification token is required")
    /** Field description. */
    String token
) {}
