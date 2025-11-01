package com.trc.platform.usage.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UsageSummaryResponse {

    /** Number of requests made today. */
    private Integer today;

    /** Number of requests made yesterday. */
    private Integer yesterday;

    /** Number of requests made in the last 7 days. */
    private Integer last7Days;

    /** Number of requests made this month. */
    private Integer thisMonth;

    /** ISO timestamp of the last request, or null if no requests. */
    private String lastRequestAt;
}
