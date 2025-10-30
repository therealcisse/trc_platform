package com.trc.platform.users.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Builder;

@Builder
public record LoginRequest(
        @NotBlank @Email @Size(max = 255) @JsonProperty("email")
                /** Field description. */
                String email,
        @NotBlank @Size(min = 8, max = 128) @JsonProperty("password")
                /** Field description. */
                String password) {}
