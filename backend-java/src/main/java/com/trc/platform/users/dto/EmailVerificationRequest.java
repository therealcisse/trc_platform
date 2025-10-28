/* (C) 2025 */
package com.trc.platform.users.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class EmailVerificationRequest {
  @NotBlank(message = "Verification token is required")
  private String token;
}
