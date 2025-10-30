package com.trc.platform.users.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record RegistrationRequest(
    @NotBlank
    @Email
    @Size(max = 255)
    /** Field description. */
    String email,

    @NotBlank
    @Size(min = 8, max = 128)
    /** Field description. */
    String password,

    @NotBlank
    @Size(min = 8, max = 128)
    /** Field description. */
    String confirmPassword,

    @NotBlank
    @Size(max = 32)
    /** Field description. */
    String inviteCode,

    @NotNull
    Boolean userAcceptedTerms,

    @NotNull
    Boolean userAcknowledgedDisclaimer
) {}
