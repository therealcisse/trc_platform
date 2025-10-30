package com.trc.platform.usage.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.trc.platform.usage.entity.BillingPeriod;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.UUID;
import lombok.Builder;

@Builder
public record CurrentBillingResponse(
        /** Field description. */
        UUID id,
        @JsonProperty("isCurrent")
                /** Field description. */
                Boolean isCurrent,
        @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd")
                @JsonProperty("periodStart")
                /** Field description. */
                LocalDate periodStart,
        @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd")
                @JsonProperty("periodEnd")
                /** Field description. */
                LocalDate periodEnd,
        @JsonProperty("periodLabel")
                /** Field description. */
                String periodLabel,
        @JsonProperty("paymentStatus")
                /** Field description. */
                String paymentStatus,
        @JsonProperty("totalRequests")
                /** Field description. */
                Integer totalRequests,
        @JsonProperty("totalCostCents")
                /** Field description. */
                Integer totalCostCents) {
    /** Field description. */
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
