/* (C) 2025 */
package com.trc.platform.users.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LoginRequest {
  @NotBlank
  @Email
  @Size(max = 255)
  @JsonProperty("email")
  private String email;

  @NotBlank
  @Size(min = 8, max = 128)
  @JsonProperty("password")
  private String password;
}
