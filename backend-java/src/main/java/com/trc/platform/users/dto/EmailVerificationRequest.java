package com.trc.platform.users.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Builder;

@Builder
public record EmailVerificationRequest(
        @NotBlank(message = "Verification token is required") String token) {}
