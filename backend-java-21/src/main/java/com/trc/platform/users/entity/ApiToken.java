package com.trc.platform.users.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;
import lombok.*;
import org.hibernate.annotations.GenericGenerator;

@Entity
@Table(name = "api_tokens")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ApiToken {

    @Id
    @GeneratedValue(generator = "UUID")
    @GenericGenerator(name = "UUID", strategy = "org.hibernate.id.UUIDGenerator")
    /** Field description. */
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    /** Field description. */
    private User user;

    @Column(name = "token_hash", unique = true, nullable = false)
    /** Field description. */
    private String tokenHash;

    @Column(name = "token_prefix", nullable = false)
    /** Field description. */
    private String tokenPrefix;

    @Column(name = "name", nullable = false)
    /** Field description. */
    private String name;

    @Column(name = "created_at", nullable = false)
    /** Field description. */
    private LocalDateTime createdAt;

    @Column(name = "last_used_at")
    /** Field description. */
    private LocalDateTime lastUsedAt;

    @Column(name = "expires_at")
    /** Field description. */
    private LocalDateTime expiresAt;

    @Column(name = "revoked_at")
    /** Field description. */
    private LocalDateTime revokedAt;

    @OneToMany(mappedBy = "token", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    @Builder.Default
    /** Field description. */
    private Set<com.trc.platform.usage.entity.RequestLog> requestLogs = new HashSet<>();

    /** Field description. */
    public boolean isRevoked() {
        return revokedAt != null;
    }
}
