package com.trc.platform.usage.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.trc.platform.usage.entity.BillingPeriod;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.UUID;

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
    Integer totalCostCents
) {
    /** Field description. */
    public static CurrentBillingResponse fromMockData() {
        LocalDate now = LocalDate.now();
        String periodLabel = now.format(DateTimeFormatter.ofPattern("MMMM yyyy"));

        return new CurrentBillingResponse(
                UUID.randomUUID(),
                true,
                now.withDayOfMonth(1),
                now.withDayOfMonth(now.lengthOfMonth()),
                periodLabel,
                BillingPeriod.PaymentStatus.pending.name(),
                90,
                4500
        );
    }
}
