package com.trc.platform.users.repository;

import com.trc.platform.users.entity.ApiToken;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

public interface ApiTokenRepository extends JpaRepository<ApiToken, UUID> {
    Optional<ApiToken> findByIdAndUserId(UUID id, UUID userId);

    @Query("SELECT t FROM ApiToken t WHERE t.tokenHash = :hash")
    Optional<ApiToken> findByTokenHash(String hash);

    @Query("SELECT t FROM ApiToken t LEFT JOIN FETCH t.user WHERE t.tokenPrefix = :prefix")
    Optional<ApiToken> findByTokenPrefix(String prefix);

    Page<ApiToken> findByUserId(UUID userId, Pageable pageable);
}
