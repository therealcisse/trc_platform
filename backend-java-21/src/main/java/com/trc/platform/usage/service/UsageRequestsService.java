package com.trc.platform.usage.service;

import com.trc.platform.usage.dto.RequestLogResponse;
import com.trc.platform.usage.entity.RequestLog;
import com.trc.platform.usage.repository.RequestLogRepository;
import com.trc.platform.users.entity.User;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class UsageRequestsService {

    private final RequestLogRepository requestLogRepository;

    private static final DateTimeFormatter DATE_TIME_FORMATTER =
            DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final DateTimeFormatter DATE_FORMATTER =
            DateTimeFormatter.ofPattern("yyyy-MM-dd");

    /**
     * Get paginated user requests with optional date filtering.
     *
     * @param user the user to get requests for
     * @param fromDate optional start date filter (ISO format)
     * @param toDate optional end date filter (ISO format)
     * @param pageable pagination information
     * @return paginated list of request logs
     */
    public Page<RequestLogResponse> getUserRequests(
            User user, String fromDate, String toDate, Pageable pageable) {

        LocalDateTime startDate = parseDate(fromDate);
        LocalDateTime endDate = parseDate(toDate);

        Page<RequestLog> requestLogs;

        if (startDate != null && endDate != null) {
            // Both dates provided - filter between range
            requestLogs =
                    requestLogRepository.findByUserAndRequestTsBetweenOrderByRequestTsDesc(
                            user, startDate, endDate, pageable);
        } else if (startDate != null) {
            // Only start date provided - filter from start date onwards
            requestLogs =
                    requestLogRepository.findByUserAndRequestTsAfterOrderByRequestTsDesc(
                            user, startDate, pageable);
        } else {
            // No date filtering - get all user requests
            requestLogs = requestLogRepository.findByUserOrderByRequestTsDesc(user, pageable);
        }

        return requestLogs.map(this::toDto);
    }

    /** Convert RequestLog entity to DTO. */
    private RequestLogResponse toDto(RequestLog requestLog) {
        return RequestLogResponse.builder()
                .id(requestLog.getId())
                .requestTs(requestLog.getRequestTs())
                .service(requestLog.getService())
                .status(requestLog.getStatus())
                .durationMs(requestLog.getDurationMs())
                .requestBytes(requestLog.getRequestBytes())
                .responseBytes(requestLog.getResponseBytes())
                .requestId(requestLog.getRequestId())
                .flowId(requestLog.getFlowId())
                .tokenPrefix(
                        Optional.ofNullable(requestLog.getToken())
                                .map(token -> token.getTokenPrefix())
                                .orElse(null))
                .build();
    }

    /**
     * Parse date string to LocalDateTime. Supports both date-only (YYYY-MM-DD) and datetime
     * (YYYY-MM-DD HH:mm:ss) formats.
     */
    private LocalDateTime parseDate(String dateString) {
        if (dateString == null || dateString.trim().isEmpty()) {
            return null;
        }

        try {
            // Try datetime format first (YYYY-MM-DD HH:mm:ss)
            return LocalDateTime.parse(dateString, DATE_TIME_FORMATTER);
        } catch (DateTimeParseException e1) {
            try {
                // Try date-only format (YYYY-MM-DD) - use start of day
                LocalDate date = LocalDate.parse(dateString, DATE_FORMATTER);
                return date.atStartOfDay();
            } catch (DateTimeParseException e2) {
                try {
                    // Try ISO datetime format (YYYY-MM-DDTHH:mm:ss)
                    return LocalDateTime.parse(dateString);
                } catch (DateTimeParseException e3) {
                    throw new IllegalArgumentException(
                            "Invalid date format. Use YYYY-MM-DD or YYYY-MM-DD HH:mm:ss or ISO"
                                    + " format",
                            e3);
                }
            }
        }
    }
}
