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
        /** Field description. */
        UUID id,
        @JsonProperty("periodLabel")
                /** Field description. */
                String periodLabel,
        @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd")
                @JsonProperty("periodStart")
                /** Field description. */
                LocalDate periodStart,
        @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd")
                @JsonProperty("periodEnd")
                /** Field description. */
                LocalDate periodEnd,
        @JsonProperty("totalRequests")
                /** Field description. */
                Integer totalRequests,
        @JsonProperty("totalCostCents")
                /** Field description. */
                Integer totalCostCents,
        @JsonProperty("isCurrent")
                /** Field description. */
                Boolean isCurrent,
        @JsonProperty("paymentStatus")
                /** Field description. */
                String paymentStatus,
        @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss.SSSSSSXXX")
                @JsonProperty("paidAt")
                /** Field description. */
                LocalDateTime paidAt,
        @JsonProperty("paidAmountCents")
                /** Field description. */
                Integer paidAmountCents,
        @JsonProperty("paymentReference")
                /** Field description. */
                String paymentReference) {
    /** Field description. */
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

    /** Field description. */
    private static String formatPeriodLabel(LocalDate periodStart) {
        return periodStart.format(DateTimeFormatter.ofPattern("MMMM yyyy"));
    }
}
