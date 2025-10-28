/* (C) 2025 */
package com.trc.platform.users.dto;

import jakarta.validation.constraints.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ResendVerificationRequest {
  @NotBlank(message = "Email is required")
  @Email(message = "Invalid email format")
  private String email;
}
