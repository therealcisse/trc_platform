package com.trc.platform.usage.dto;

import com.trc.platform.usage.entity.PaymentStatus;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.trc.platform.usage.entity.BillingPeriod;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.UUID;
import lombok.Builder;

@Builder
public record CurrentBillingResponse(
        UUID id,
        @JsonProperty("isCurrent") Boolean isCurrent,
        @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd")
                @JsonProperty("periodStart")
                LocalDate periodStart,
        @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd")
                @JsonProperty("periodEnd")
                LocalDate periodEnd,
        @JsonProperty("periodLabel") String periodLabel,
        @JsonProperty("paymentStatus") String paymentStatus,
        @JsonProperty("totalRequests") Integer totalRequests,
        @JsonProperty("totalCostCents") Integer totalCostCents) {
    public static CurrentBillingResponse fromMockData() {
        LocalDate now = LocalDate.now();
        String periodLabel = now.format(DateTimeFormatter.ofPattern("MMMM yyyy"));

        return CurrentBillingResponse.builder()
                .id(UUID.randomUUID())
                .isCurrent(true)
                .periodStart(now.withDayOfMonth(1))
                .periodEnd(now.withDayOfMonth(now.lengthOfMonth()))
                .periodLabel(periodLabel)
                .paymentStatus(PaymentStatus.pending.name())
                .totalRequests(90)
                .totalCostCents(4500)
                .build();
    }
}
