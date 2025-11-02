package com.trc.platform.users.service;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import javax.crypto.SecretKey;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
@Slf4j
public class JwtEmailVerificationService {

    private final SecretKey signingKey;

    private static final long TOKEN_EXPIRY_HOURS = 24;

    public JwtEmailVerificationService(@Value("${email.verification.secret}") String secret) {
        // Ensure the secret is at least 256 bits for HS256
        if (secret.length() < 32) {
            throw new IllegalArgumentException(
                    "Email verification secret must be at least 32 characters");
        }
        this.signingKey = Keys.hmacShaKeyFor(secret.getBytes());
        log.info("JWT Email Verification Service initialized with secure signing key");
    }

    public String generateVerificationToken(String email) {
        Instant now = Instant.now();
        Instant expiry = now.plus(TOKEN_EXPIRY_HOURS, ChronoUnit.HOURS);

        return Jwts.builder()
                .setSubject(email)
                .setIssuedAt(Date.from(now))
                .setExpiration(Date.from(expiry))
                .signWith(signingKey, SignatureAlgorithm.HS256)
                .compact();
    }

    public boolean validateVerificationToken(String token) {
        try {
            Jwts.parserBuilder().setSigningKey(signingKey).build().parseClaimsJws(token);
            return true;
        } catch (ExpiredJwtException e) {
            log.warn("Email verification token expired: {}", e.getMessage());
            return false;
        } catch (UnsupportedJwtException e) {
            log.warn("Unsupported email verification token: {}", e.getMessage());
            return false;
        } catch (MalformedJwtException e) {
            log.warn("Malformed email verification token: {}", e.getMessage());
            return false;
        } catch (SecurityException e) {
            log.warn("Invalid email verification token signature: {}", e.getMessage());
            return false;
        } catch (IllegalArgumentException e) {
            log.warn("Invalid email verification token: {}", e.getMessage());
            return false;
        } catch (JwtException e) {
            log.warn("JWT validation failed: {}", e.getMessage());
            return false;
        }
    }

    public String extractEmailFromToken(String token) {
        try {
            Claims claims =
                    Jwts.parserBuilder()
                            .setSigningKey(signingKey)
                            .build()
                            .parseClaimsJws(token)
                            .getBody();
            return claims.getSubject();
        } catch (JwtException | IllegalArgumentException e) {
            log.warn("Failed to extract email from token: {}", e.getMessage());
            return null;
        }
    }

    public boolean isTokenExpired(String token) {
        try {
            Claims claims =
                    Jwts.parserBuilder()
                            .setSigningKey(signingKey)
                            .build()
                            .parseClaimsJws(token)
                            .getBody();
            return claims.getExpiration().before(new Date());
        } catch (JwtException | IllegalArgumentException e) {
            return true; // If we can't parse, consider it expired
        }
    }

    public Instant getTokenExpiration(String token) {
        try {
            Claims claims =
                    Jwts.parserBuilder()
                            .setSigningKey(signingKey)
                            .build()
                            .parseClaimsJws(token)
                            .getBody();
            return claims.getExpiration().toInstant();
        } catch (JwtException | IllegalArgumentException e) {
            return null;
        }
    }
}
