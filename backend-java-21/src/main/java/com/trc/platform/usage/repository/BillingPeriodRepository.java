package com.trc.platform.usage.repository;

import com.trc.platform.usage.entity.BillingPeriod;
import com.trc.platform.usage.entity.RequestLog;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.*;
import org.springframework.data.jpa.repository.*;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface BillingPeriodRepository extends JpaRepository<BillingPeriod, UUID> {

    @Query(
            "SELECT bp FROM BillingPeriod bp WHERE bp.user.id = :userId ORDER BY bp.periodStart"
                    + " DESC")
    Page<BillingPeriod> findByUserIdOrderByPeriodStart(
            @Param("userId") UUID userId, Pageable pageable);

    @Query("SELECT bp FROM BillingPeriod bp WHERE bp.user.id = :userId AND bp.current = true")
    Optional<BillingPeriod> findCurrentByUserId(@Param("userId") UUID userId);

    @Query("SELECT bp FROM BillingPeriod bp WHERE bp.user.id = :userId AND bp.id = :periodId")
    Optional<BillingPeriod> findByUserIdAndId(
            @Param("userId") UUID userId, @Param("periodId") UUID periodId);

    @Query(
            "SELECT rl FROM RequestLog rl WHERE rl.billingPeriod.id = :periodId ORDER BY"
                    + " rl.requestTs DESC")
    List<RequestLog> findRequestsByPeriodId(@Param("periodId") UUID periodId);

    @Query("SELECT COUNT(rl) FROM RequestLog rl WHERE rl.billingPeriod.id = :periodId")
    Long countRequestsByPeriodId(@Param("periodId") UUID periodId);

    @Query("SELECT MAX(rl.requestTs) FROM RequestLog rl WHERE rl.billingPeriod.id = :periodId")
    LocalDateTime findLastRequestTimeByPeriodId(@Param("periodId") UUID periodId);

    @Query(
            "SELECT bp FROM BillingPeriod bp WHERE bp.user.id = :userId AND bp.periodStart ="
                    + " :periodStart")
    Optional<BillingPeriod> findByUserIdAndPeriodStart(
            @Param("userId") UUID userId, @Param("periodStart") java.time.LocalDate periodStart);
}
