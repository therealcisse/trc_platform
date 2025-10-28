/* (C) 2025 */
package com.trc.platform.admin.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Future;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class CreateInviteCodeRequest {
  @Size(min = 6, max = 32)
  @JsonProperty("code")
  private String code;

  @Future(message = "expiresAt must be in the future")
  @JsonProperty("expiresAt")
  @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss")
  private java.time.LocalDateTime expiresAt;
}
