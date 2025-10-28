/* (C) 2025 */
package com.trc.platform.usage.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.trc.platform.usage.entity.BillingPeriod;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.UUID;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class BillingPeriodResponse {
  private UUID id;

  @JsonProperty("periodLabel")
  private String periodLabel;

  @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd")
  @JsonProperty("periodStart")
  private LocalDate periodStart;

  @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd")
  @JsonProperty("periodEnd")
  private LocalDate periodEnd;

  @JsonProperty("totalRequests")
  private Integer totalRequests;

  @JsonProperty("totalCostCents")
  private Integer totalCostCents;

  @JsonProperty("isCurrent")
  private Boolean isCurrent;

  @JsonProperty("paymentStatus")
  private String paymentStatus;

  @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss.SSSSSSXXX")
  @JsonProperty("paidAt")
  private LocalDateTime paidAt;

  @JsonProperty("paidAmountCents")
  private Integer paidAmountCents;

  @JsonProperty("paymentReference")
  private String paymentReference;

  public static BillingPeriodResponse fromEntity(BillingPeriod entity) {
    return BillingPeriodResponse.builder()
        .id(entity.getId())
        .periodLabel(formatPeriodLabel(entity.getPeriodStart()))
        .periodStart(entity.getPeriodStart())
        .periodEnd(entity.getPeriodEnd())
        .totalRequests(entity.getTotalRequests())
        .totalCostCents(entity.getTotalCostCents())
        .isCurrent(entity.getCurrent())
        .paymentStatus(entity.getPaymentStatus().name())
        .paidAt(entity.getPaidAt())
        .paidAmountCents(entity.getPaidAmountCents())
        .paymentReference(entity.getPaymentReference())
        .build();
  }

  private static String formatPeriodLabel(LocalDate periodStart) {
    return periodStart.format(DateTimeFormatter.ofPattern("MMMM yyyy"));
  }
}
