/* (C) 2025 */
package com.trc.platform.admin.dto;

import com.trc.platform.usage.entity.BillingPeriod;
import java.time.LocalDateTime;
import java.util.UUID;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class BillingPeriodAdminResponse {
  private UUID id;
  private UUID userId;
  private BillingPeriod.PaymentStatus paymentStatus;
  private Boolean current;
  private Integer totalRequests;
  private Integer totalCostCents;
  private LocalDateTime paidAt;
  private Integer paidAmountCents;
  private String paymentReference;
  private String notes;
}
