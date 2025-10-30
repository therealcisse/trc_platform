package com.trc.platform.admin.dto;

import com.trc.platform.usage.entity.BillingPeriod;
import java.time.LocalDateTime;
import java.util.UUID;
import lombok.Builder;

@Builder
public record BillingPeriodAdminResponse(
        /** Field description. */
        UUID id,

        /** Field description. */
        UUID userId,
        BillingPeriod.PaymentStatus paymentStatus,

        /** Field description. */
        Boolean current,

        /** Field description. */
        Integer totalRequests,

        /** Field description. */
        Integer totalCostCents,

        /** Field description. */
        LocalDateTime paidAt,

        /** Field description. */
        Integer paidAmountCents,

        /** Field description. */
        String paymentReference,

        /** Field description. */
        String notes) {}
