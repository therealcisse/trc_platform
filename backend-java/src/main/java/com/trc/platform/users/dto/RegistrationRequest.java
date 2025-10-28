/* (C) 2025 */
package com.trc.platform.users.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class RegistrationRequest {
  @NotBlank
  @Email
  @Size(max = 255)
  private String email;

  @NotBlank
  @Size(min = 8, max = 128)
  private String password;

  @NotBlank
  @Size(min = 8, max = 128)
  private String confirmPassword;

  @NotBlank
  @Size(max = 32)
  private String inviteCode;

  @NotNull private Boolean userAcceptedTerms;

  @NotNull private Boolean userAcknowledgedDisclaimer;
}
