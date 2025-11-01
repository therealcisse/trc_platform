package com.trc.platform.users.dto;

import jakarta.validation.constraints.*;
import lombok.Builder;

@Builder
public record ResendVerificationRequest(
        @NotBlank(message = "Email is required") @Email(message = "Invalid email format")
                String email) {}
