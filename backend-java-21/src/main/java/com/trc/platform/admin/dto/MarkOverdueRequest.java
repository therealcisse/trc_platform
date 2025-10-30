package com.trc.platform.admin.dto;

import lombok.Builder;

@Builder
public record MarkOverdueRequest(
        /** Field description. */
        String notes) {}
