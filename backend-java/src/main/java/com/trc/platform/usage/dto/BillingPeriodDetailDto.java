/* (C) 2025 */
package com.trc.platform.usage.dto;

import com.trc.platform.usage.entity.BillingPeriod;
import java.time.LocalDate;
import java.util.List;
import java.util.UUID;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class BillingPeriodDetailDto {
  private UUID id;
  private LocalDate periodStart;
  private LocalDate periodEnd;
  private Integer totalRequests;
  private Integer totalCostCents;
  private BillingPeriod.PaymentStatus paymentStatus;
  private Boolean current;
  private List<RequestLogDto> requests;

  @Data
  @Builder
  public static class RequestLogDto {
    private UUID id;
    private String status;
    private Integer durationMs;
    private String flowId;
    private String result;
  }
}
