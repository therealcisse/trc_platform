package com.trc.platform.usage.entity;

import com.trc.platform.users.entity.ApiToken;
import com.trc.platform.users.entity.User;
import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.UUID;
import lombok.*;
import org.hibernate.annotations.GenericGenerator;

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

    /** Field description. */
    public enum RequestStatus {
        SUCCESS,
        ERROR
    }

    @Id
    @GeneratedValue(generator = "UUID")
    @GenericGenerator(name = "UUID", strategy = "org.hibernate.id.UUIDGenerator")
    /** Field description. */
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    /** Field description. */
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "token_id")
    /** Field description. */
    private ApiToken token;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "billing_period_id")
    /** Field description. */
    private BillingPeriod billingPeriod;

    @Column(name = "service", nullable = false)
    /** Field description. */
    private String service = "core.image_solve";

    @Column(name = "request_ts", nullable = false)
    /** Field description. */
    private LocalDateTime requestTs;

    @Column(name = "duration_ms", nullable = false)
    /** Field description. */
    private Integer durationMs;

    @Column(name = "request_bytes", nullable = false)
    /** Field description. */
    private Integer requestBytes;

    @Column(name = "response_bytes", nullable = false)
    /** Field description. */
    private Integer responseBytes;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    /** Field description. */
    private RequestStatus status;

    @Column(name = "error_code", length = 50)
    /** Field description. */
    private String errorCode;

    @Column(name = "request_id", nullable = false)
    /** Field description. */
    private UUID requestId;

    @Column(name = "flow_id", length = 255)
    /** Field description. */
    private String flowId;

    @Column(name = "result", columnDefinition = "TEXT")
    /** Field description. */
    private String result;
}
