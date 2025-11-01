package com.trc.platform.usage.entity;

import com.trc.platform.users.entity.ApiToken;
import com.trc.platform.users.entity.User;
import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.UUID;
import lombok.*;
import org.hibernate.annotations.GenericGenerator;
import org.hibernate.annotations.JdbcType;
import org.hibernate.dialect.PostgreSQLEnumJdbcType;

@Entity
@Table(
        name = "request_logs",
        indexes = {
            @Index(name = "idx_user_timestamp", columnList = "user_id, request_ts"),
            @Index(name = "idx_request_ts", columnList = "request_ts"),
            @Index(name = "idx_request_id", columnList = "request_id"),
            @Index(name = "idx_flow_id", columnList = "flow_id")
        })
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class RequestLog {

    public enum RequestStatus {
        SUCCESS,
        ERROR
    }

    @Id
    @GeneratedValue(generator = "UUID")
    @GenericGenerator(name = "UUID", strategy = "org.hibernate.id.UUIDGenerator")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "token_id")
    private ApiToken token;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "billing_period_id")
    private BillingPeriod billingPeriod;

    @Column(name = "service", nullable = false)
    private String service = "core.image_solve";

    @Column(name = "request_ts", nullable = false)
    private LocalDateTime requestTs;

    @Column(name = "duration_ms", nullable = false)
    private Integer durationMs;

    @Column(name = "request_bytes", nullable = false)
    private Integer requestBytes;

    @Column(name = "response_bytes", nullable = false)
    private Integer responseBytes;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    @JdbcType(PostgreSQLEnumJdbcType.class)
    private RequestStatus status;

    @Column(name = "error_code", length = 50)
    private String errorCode;

    @Column(name = "request_id", nullable = false)
    private UUID requestId;

    @Column(name = "flow_id", length = 255)
    private String flowId;

    @Column(name = "result", columnDefinition = "TEXT")
    private String result;
}
