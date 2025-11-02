package com.trc.platform.admin.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.trc.platform.usage.entity.BillingPeriod;
import java.time.LocalDateTime;
import java.util.UUID;
import lombok.Builder;

@Builder
public record BillingPeriodAdminResponse(
        UUID id,
        UUID userId,
        BillingPeriod.PaymentStatus paymentStatus,
        Boolean current,
        Integer totalRequests,
        Integer totalCostCents,
        @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS")
        LocalDateTime paidAt,
        Integer paidAmountCents,
        String paymentReference,
        String notes) {}
