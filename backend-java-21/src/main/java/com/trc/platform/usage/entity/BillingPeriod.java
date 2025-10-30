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

    /** Field description. */
    public enum PaymentStatus {
        pending,
        paid,
        overdue,
        waived
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

    @Column(name = "period_start", nullable = false)
    /** Field description. */
    private LocalDate periodStart;

    @Column(name = "period_end", nullable = false)
    /** Field description. */
    private LocalDate periodEnd;

    @Column(name = "total_requests", nullable = false)
    /** Field description. */
    private Integer totalRequests = 0;

    @Column(name = "total_cost_cents", nullable = false)
    /** Field description. */
    private Integer totalCostCents = 0;

    @Column(name = "is_current", nullable = false)
    /** Field description. */
    private Boolean current = false;

    @Enumerated(EnumType.STRING)
    @Column(name = "payment_status", nullable = false)
    /** Field description. */
    private PaymentStatus paymentStatus = PaymentStatus.pending;

    @Column(name = "paid_at")
    /** Field description. */
    private LocalDateTime paidAt;

    @Column(name = "paid_amount_cents")
    /** Field description. */
    private Integer paidAmountCents;

    @Column(name = "payment_reference", length = 255)
    /** Field description. */
    private String paymentReference;

    @Column(name = "notes", columnDefinition = "TEXT")
    /** Field description. */
    private String notes;

    @Version private Long version;

    @OneToMany(mappedBy = "billingPeriod", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    @Builder.Default
    /** Field description. */
    private Set<RequestLog> requests = new HashSet<>();
}
