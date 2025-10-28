/* (C) 2025 */
package com.trc.platform.usage.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.trc.platform.usage.entity.BillingPeriod;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.UUID;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class CurrentBillingResponse {
  private UUID id;

  @JsonProperty("isCurrent")
  private Boolean isCurrent;

  @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd")
  @JsonProperty("periodStart")
  private LocalDate periodStart;

  @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd")
  @JsonProperty("periodEnd")
  private LocalDate periodEnd;

  @JsonProperty("periodLabel")
  private String periodLabel;

  @JsonProperty("paymentStatus")
  private String paymentStatus;

  @JsonProperty("totalRequests")
  private Integer totalRequests;

  @JsonProperty("totalCostCents")
  private Integer totalCostCents;

  public static CurrentBillingResponse fromMockData() {
    LocalDate now = LocalDate.now();
    String periodLabel = now.format(DateTimeFormatter.ofPattern("MMMM yyyy"));

    return CurrentBillingResponse.builder()
        .id(UUID.randomUUID())
        .isCurrent(true)
        .periodStart(now.withDayOfMonth(1))
        .periodEnd(now.withDayOfMonth(now.lengthOfMonth()))
        .periodLabel(periodLabel)
        .paymentStatus(BillingPeriod.PaymentStatus.pending.name())
        .totalRequests(90)
        .totalCostCents(4500)
        .build();
  }
}
