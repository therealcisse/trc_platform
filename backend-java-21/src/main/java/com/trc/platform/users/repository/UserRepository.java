package com.trc.platform.users.repository;

import com.trc.platform.users.entity.User;
import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.*;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface UserRepository extends JpaRepository<User, UUID> {

    Optional<User> findByEmail(String email);

    Optional<User> findByEmailIgnoreCase(String email);

    @Query("SELECT u FROM User u WHERE u.email = :email AND u.active = true")
    Optional<User> findActiveByEmail(@Param("email") String email);

    @Modifying
    @Query("UPDATE User u SET u.passwordHash = :passwordHash WHERE u.id = :userId")
    int updatePassword(@Param("userId") UUID userId, @Param("passwordHash") String passwordHash);

    @Modifying
    @Query(
            "UPDATE User u SET u.emailVerifiedAt = :verifiedAt WHERE u.id = :userId AND u.email ="
                    + " :email")
    int verifyEmail(
            @Param("userId") UUID userId,
            @Param("email") String email,
            @Param("verifiedAt") LocalDateTime verifiedAt);
}
