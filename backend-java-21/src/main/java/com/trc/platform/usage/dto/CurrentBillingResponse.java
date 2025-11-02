package com.trc.platform.usage.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.LocalDate;
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
}
