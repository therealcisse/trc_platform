package com.trc.platform.users.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;
import lombok.Builder;

@Builder
public record CreateApiTokenRequest(
        @NotBlank(message = "Token name is required")
                @Size(
                        min = 1,
                        max = 100,
                        message = "Token name must be between 1 and 100 characters")
                String name,
        @JsonProperty("expiresAt") LocalDateTime expiresAt) {}
