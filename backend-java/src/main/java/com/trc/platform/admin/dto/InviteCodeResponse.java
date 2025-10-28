/* (C) 2025 */
package com.trc.platform.admin.dto;

import java.time.LocalDateTime;
import java.util.UUID;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class InviteCodeResponse {
  private UUID id;
  private String code;
  private Boolean active;
  private LocalDateTime createdAt;
  private LocalDateTime expiresAt;
  private LocalDateTime usedAt;
  private UUID usedByUserId;
  private UUID createdByUserId;
  private String createdByUserEmail;
}
