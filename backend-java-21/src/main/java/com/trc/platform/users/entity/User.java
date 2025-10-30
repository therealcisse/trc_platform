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
    /** Field description. */
    private UUID id;

    @Column(unique = true, nullable = false)
    /** Field description. */
    private String email;

    @Column(nullable = false, name = "password_hash")
    /** Field description. */
    private String passwordHash;

    @Column(name = "is_active", nullable = false)
    /** Field description. */
    private Boolean active = true;

    @Column(name = "is_staff", nullable = false)
    /** Field description. */
    private Boolean staff = false;

    @Column(name = "email_verified_at")
    /** Field description. */
    private LocalDateTime emailVerifiedAt;

    @Column(name = "date_joined", nullable = false)
    /** Field description. */
    private LocalDateTime dateJoined;

    @Column(name = "user_accepted_terms", nullable = false)
    /** Field description. */
    private Boolean userAcceptedTerms = false;

    @Column(name = "user_acknowledged_disclaimer", nullable = false)
    /** Field description. */
    private Boolean userAcknowledgedDisclaimer = false;

    @Version private Long version;

    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    @Builder.Default
    /** Field description. */
    private Set<ApiToken> apiTokens = new HashSet<>();

    /** Field description. */
    public boolean isEmailVerified() {
        return emailVerifiedAt != null;
    }

    /** Field description. */
    public boolean hasAcceptedTerms() {
        return Boolean.TRUE.equals(userAcceptedTerms);
    }

    /** Field description. */
    public boolean hasAcknowledgedDisclaimer() {
        return Boolean.TRUE.equals(userAcknowledgedDisclaimer);
    }
}
