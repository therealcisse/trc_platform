package com.trc.platform.users.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;
import lombok.*;
import org.hibernate.annotations.GenericGenerator;

@Entity
@Table(name = "users")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class User {

    @Id
    @GeneratedValue(generator = "UUID")
    @GenericGenerator(name = "UUID", strategy = "org.hibernate.id.UUIDGenerator")
    private UUID id;

    @Column(unique = true, nullable = false)
    private String email;

    @Column(nullable = false, name = "password_hash")
    private String passwordHash;

    @Column(name = "is_active", nullable = false)
    private Boolean active = true;

    @Column(name = "is_staff", nullable = false)
    private Boolean staff = false;

    @Column(name = "email_verified_at")
    private LocalDateTime emailVerifiedAt;

    @Column(name = "date_joined", nullable = false)
    private LocalDateTime dateJoined;

    @Column(name = "user_accepted_terms", nullable = false)
    private Boolean userAcceptedTerms = false;

    @Column(name = "user_acknowledged_disclaimer", nullable = false)
    private Boolean userAcknowledgedDisclaimer = false;

    @Version private Long version;

    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    @Builder.Default
    private Set<ApiToken> apiTokens = new HashSet<>();

    public boolean isEmailVerified() {
        return emailVerifiedAt != null;
    }

    public boolean hasAcceptedTerms() {
        return Boolean.TRUE.equals(userAcceptedTerms);
    }

    public boolean hasAcknowledgedDisclaimer() {
        return Boolean.TRUE.equals(userAcknowledgedDisclaimer);
    }
}
