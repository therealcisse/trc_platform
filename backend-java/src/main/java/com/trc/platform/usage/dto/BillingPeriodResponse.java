package com.trc.platform.usage.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.trc.platform.usage.entity.BillingPeriod;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.UUID;
import lombok.Builder;

@Builder
public record BillingPeriodResponse(
        UUID id,
        @JsonProperty("periodLabel") String periodLabel,
        @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd")
                @JsonProperty("periodStart")
                LocalDate periodStart,
        @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd")
                @JsonProperty("periodEnd")
                LocalDate periodEnd,
        @JsonProperty("totalRequests") Integer totalRequests,
        @JsonProperty("totalCostCents") Integer totalCostCents,
        @JsonProperty("isCurrent") Boolean isCurrent,
        @JsonProperty("paymentStatus") String paymentStatus,
        @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS")
                @JsonProperty("paidAt")
                LocalDateTime paidAt,
        @JsonProperty("paidAmountCents") Integer paidAmountCents,
        @JsonProperty("paymentReference") String paymentReference) {
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
