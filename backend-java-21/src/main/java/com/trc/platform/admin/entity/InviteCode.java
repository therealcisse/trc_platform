package com.trc.platform.admin.entity;

import com.trc.platform.users.entity.User;
import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.UUID;
import lombok.*;
import org.hibernate.annotations.GenericGenerator;

@Entity
@Table(
        name = "invite_codes",
        indexes = {@Index(name = "idx_code", columnList = "code")})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class InviteCode {

    @Id
    @GeneratedValue(generator = "UUID")
    @GenericGenerator(name = "UUID", strategy = "org.hibernate.id.UUIDGenerator")
    /** Field description. */
    private UUID id;

    @Column(name = "code", unique = true, nullable = false, length = 32)
    /** Field description. */
    private String code;

    @Column(name = "is_active", nullable = false)
    /** Field description. */
    private Boolean active = true;

    @Column(name = "expires_at")
    /** Field description. */
    private LocalDateTime expiresAt;

    @Column(name = "created_at", nullable = false)
    /** Field description. */
    private LocalDateTime createdAt;

    @Column(name = "used_at")
    /** Field description. */
    private LocalDateTime usedAt;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "created_by_user_id")
    /** Field description. */
    private User createdByUser;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "used_by_user_id")
    /** Field description. */
    private User usedBy;

    @PrePersist
    /** Field description. */
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = LocalDateTime.now();
        }
    }

    /** Field description. */
    public boolean isExpired() {
        return expiresAt != null && LocalDateTime.now().isAfter(expiresAt);
    }

    /** Field description. */
    public boolean isValid() {
        return active && !isExpired() && usedBy == null;
    }

    /** Field description. */
    public void markAsUsed(User user) {
        this.usedBy = user;
        this.usedAt = LocalDateTime.now();
    }
}
