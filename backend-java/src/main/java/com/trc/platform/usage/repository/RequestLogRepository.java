package com.trc.platform.usage.repository;

import com.trc.platform.usage.entity.RequestLog;
import com.trc.platform.users.entity.User;
import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface RequestLogRepository extends JpaRepository<RequestLog, UUID> {

    @Query(
            "SELECT COUNT(rl) FROM RequestLog rl WHERE rl.user = :user AND rl.requestTs >="
                    + " :startTime")
    Long countByUserAndRequestTsAfter(
            @Param("user") User user, @Param("startTime") LocalDateTime startTime);

    @Query(
            "SELECT COUNT(rl) FROM RequestLog rl WHERE rl.user = :user AND rl.requestTs >="
                    + " :startTime AND rl.requestTs < :endTime")
    Long countByUserAndRequestTsBetween(
            @Param("user") User user,
            @Param("startTime") LocalDateTime startTime,
            @Param("endTime") LocalDateTime endTime);

    @Query("SELECT rl FROM RequestLog rl WHERE rl.user = :user ORDER BY rl.requestTs DESC FETCH FIRST 1 ROW ONLY")
    Optional<RequestLog> findLastByUser(@Param("user") User user);

    @Query("SELECT MAX(rl.requestTs) FROM RequestLog rl WHERE rl.user = :user")
    LocalDateTime findLastRequestTimeByUser(@Param("user") User user);

    Page<RequestLog> findByUserOrderByRequestTsDesc(User user, Pageable pageable);

    @Query(
            "SELECT rl FROM RequestLog rl WHERE rl.user = :user AND rl.requestTs >= :startTime"
                    + " ORDER BY rl.requestTs DESC")
    Page<RequestLog> findByUserAndRequestTsAfterOrderByRequestTsDesc(
            @Param("user") User user,
            @Param("startTime") LocalDateTime startTime,
            Pageable pageable);

    @Query(
            "SELECT rl FROM RequestLog rl WHERE rl.user = :user AND rl.requestTs >= :startTime"
                    + " AND rl.requestTs <= :endTime ORDER BY rl.requestTs DESC")
    Page<RequestLog> findByUserAndRequestTsBetweenOrderByRequestTsDesc(
            @Param("user") User user,
            @Param("startTime") LocalDateTime startTime,
            @Param("endTime") LocalDateTime endTime,
            Pageable pageable);
}
