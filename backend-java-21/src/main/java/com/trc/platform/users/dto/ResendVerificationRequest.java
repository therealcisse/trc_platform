package com.trc.platform.users.dto;

import jakarta.validation.constraints.*;

public record ResendVerificationRequest(
    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    /** Field description. */
    String email
) {}
