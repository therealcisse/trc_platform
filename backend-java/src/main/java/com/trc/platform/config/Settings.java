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
    private Long id = 1L;

    @Column(name = "cost_per_request_cents", nullable = false)
    private Integer costPerRequestCents = 100;

    @Column(name = "openai_model")
    private String openaiModel = "gpt-4.1-mini-2025-04-14";

    @Column(name = "openai_timeout_s", nullable = false)
    private Integer openaiTimeoutSeconds = 30;

    @Column(name = "app_domain")
    private String appDomain;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @PrePersist
    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
