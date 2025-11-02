package com.trc.platform.usage.service;

import com.trc.platform.usage.dto.UsageSummaryResponse;
import com.trc.platform.usage.entity.RequestLog;
import com.trc.platform.usage.repository.RequestLogRepository;
import com.trc.platform.users.entity.User;
import java.time.LocalDateTime;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class UsageService {

    private final RequestLogRepository requestLogRepository;

    /**
     * Get usage summary for a user similar to Django implementation.
     *
     * @param user the user to get summary for
     * @return usage summary with counts for various time periods
     */
    public UsageSummaryResponse getUsageSummary(User user) {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime today = now.withHour(0).withMinute(0).withSecond(0).withNano(0);
        LocalDateTime yesterday = today.minusDays(1);
        LocalDateTime weekAgo = today.minusDays(7);
        LocalDateTime monthStart = today.withDayOfMonth(1);

        // Today's count
        Long todayCount = requestLogRepository.countByUserAndRequestTsAfter(user, today);

        // Yesterday's count
        Long yesterdayCount =
                requestLogRepository.countByUserAndRequestTsBetween(user, yesterday, today);

        // Last 7 days count
        Long last7DaysCount = requestLogRepository.countByUserAndRequestTsAfter(user, weekAgo);

        // This month count
        Long thisMonthCount = requestLogRepository.countByUserAndRequestTsAfter(user, monthStart);

        // Get last request timestamp
        Optional<RequestLog> lastRequest = requestLogRepository.findLastByUser(user);
        String lastRequestAt =
                lastRequest.map(request -> request.getRequestTs().toString()).orElse(null);

        return UsageSummaryResponse.builder()
                .today(todayCount.intValue())
                .yesterday(yesterdayCount.intValue())
                .last7Days(last7DaysCount.intValue())
                .thisMonth(thisMonthCount.intValue())
                .lastRequestAt(lastRequestAt)
                .build();
    }
}
