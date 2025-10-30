package com.trc.platform.config;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import lombok.*;

@Entity
@Table(name = "settings")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Settings {
    @Id
    @Column(name = "id", nullable = false)
    /** Field description. */
    private Long id = 1L;

    @Column(name = "cost_per_request_cents", nullable = false)
    /** Field description. */
    private Integer costPerRequestCents = 100;

    @Column(name = "openai_model")
    /** Field description. */
    private String openaiModel = "gpt-4.1-mini-2025-04-14";

    @Column(name = "openai_timeout_s", nullable = false)
    /** Field description. */
    private Integer openaiTimeoutSeconds = 30;

    @Column(name = "app_domain")
    /** Field description. */
    private String appDomain;

    @Column(name = "updated_at", nullable = false)
    /** Field description. */
    private LocalDateTime updatedAt;

    @PrePersist
    @PreUpdate
    /** Field description. */
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
