package com.trc.platform.admin.repository;

import com.trc.platform.admin.entity.InviteCode;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.*;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface InviteCodeRepository extends JpaRepository<InviteCode, UUID> {

    Optional<InviteCode> findByCodeAndActiveTrue(String code);

    Optional<InviteCode> findByCodeAndActiveTrueAndUsedByIsNull(String code);

    Optional<InviteCode> findByCode(String code);

    @Query("SELECT ic FROM InviteCode ic WHERE ic.expiresAt < :now AND ic.active = true")
    List<InviteCode> findExpiredCodes(@Param("now") LocalDateTime now);

    @Modifying
    @Query("DELETE FROM InviteCode ic WHERE ic.expiresAt < :now AND ic.active = true")
    int deleteExpiredCodes(@Param("now") LocalDateTime now);
}
