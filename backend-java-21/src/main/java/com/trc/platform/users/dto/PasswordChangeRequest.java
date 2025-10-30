package com.trc.platform.users.dto;

import jakarta.validation.constraints.*;
import lombok.Builder;

@Builder
public record PasswordChangeRequest(
        @NotBlank(message = "Current password is required")
                /** Field description. */
                String currentPassword,
        @NotBlank(message = "New password is required")
                @Size(min = 8, max = 128, message = "Password must be between 8 and 128 characters")
                @Pattern(
                        regexp = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&]).+$",
                        message =
                                "Password must contain uppercase, lowercase, digit, and special"
                                        + " character")
                /** Field description. */
                String newPassword,
        @NotBlank(message = "Password confirmation is required")
                /** Field description. */
                String confirmPassword) {}
