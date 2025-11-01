package com.trc.platform.usage.dto;

import com.trc.platform.usage.entity.BillingPeriod;
import java.time.LocalDate;
import java.util.List;
import java.util.UUID;
import lombok.Builder;
import com.trc.platform.usage.entity.PaymentStatus;

@Builder
public record BillingPeriodDetailDto(
        UUID id,
        LocalDate periodStart,
        LocalDate periodEnd,
        Integer totalRequests,
        Integer totalCostCents,
        PaymentStatus paymentStatus,
        Boolean current,
        List<RequestLogDto> requests) {
    @Builder
    public record RequestLogDto(
            UUID id, String status, Integer durationMs, String flowId, String result) {}
}
