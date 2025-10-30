package com.trc.platform.usage.dto;

import com.trc.platform.usage.entity.BillingPeriod;
import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

public record BillingPeriodDetailDto(
    /** Field description. */
    UUID id,

    /** Field description. */
    LocalDate periodStart,

    /** Field description. */
    LocalDate periodEnd,

    /** Field description. */
    Integer totalRequests,

    /** Field description. */
    Integer totalCostCents,

    BillingPeriod.PaymentStatus paymentStatus,

    /** Field description. */
    Boolean current,

    /** Field description. */
    List<RequestLogDto> requests
) {
    /** Field description. */
    public record RequestLogDto(
        /** Field description. */
        UUID id,

        /** Field description. */
        String status,

        /** Field description. */
        Integer durationMs,

        /** Field description. */
        String flowId,

        /** Field description. */
        String result
    ) {}
}
