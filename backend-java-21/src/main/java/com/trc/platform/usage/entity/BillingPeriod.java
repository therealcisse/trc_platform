package com.trc.platform.usage.entity;

import com.trc.platform.users.entity.User;
import jakarta.persistence.*;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;
import lombok.*;
import org.hibernate.annotations.GenericGenerator;
import org.hibernate.annotations.JdbcType;
import org.hibernate.dialect.PostgreSQLEnumJdbcType;

@Entity
@Table(
        name = "billing_periods",
        indexes = {
            @Index(name = "idx_user_period", columnList = "user_id, period_start"),
            @Index(name = "idx_current_period", columnList = "is_current")
        })
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class BillingPeriod {
    @Id
    @GeneratedValue(generator = "UUID")
    @GenericGenerator(name = "UUID", strategy = "org.hibernate.id.UUIDGenerator")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "period_start", nullable = false)
    private LocalDate periodStart;

    @Column(name = "period_end", nullable = false)
    private LocalDate periodEnd;

    @Column(name = "total_requests", nullable = false)
    private Integer totalRequests = 0;

    @Column(name = "total_cost_cents", nullable = false)
    private Integer totalCostCents = 0;

    @Column(name = "is_current", nullable = false)
    private Boolean current = false;

    @Enumerated(EnumType.STRING)
    @Column(name = "payment_status", nullable = false)
    @JdbcType(PostgreSQLEnumJdbcType.class)
    private PaymentStatus paymentStatus = PaymentStatus.pending;

    @Column(name = "paid_at")
    private LocalDateTime paidAt;

    @Column(name = "paid_amount_cents")
    private Integer paidAmountCents;

    @Column(name = "payment_reference", length = 255)
    private String paymentReference;

    @Column(name = "notes", columnDefinition = "TEXT")
    private String notes;

    @Version private Long version;

    @OneToMany(mappedBy = "billingPeriod", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    @Builder.Default
    private Set<RequestLog> requests = new HashSet<>();
}
