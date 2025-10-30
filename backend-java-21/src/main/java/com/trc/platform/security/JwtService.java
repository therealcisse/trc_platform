package com.trc.platform.security;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import java.security.Key;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import java.util.Map;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class JwtService {

    @Value("${security.jwt.secret:}")
    /** Field description. */
    private String base64Secret;

    @Value("${security.jwt.ttl-hours:24}")
    /** Field description. */
    private long ttlHours;

    /** Field description. */
    private Key key() {
        byte[] keyBytes = Decoders.BASE64.decode(base64Secret);
        return Keys.hmacShaKeyFor(keyBytes);
    }

    /** Field description. */
    public String generateSessionToken(UUID userId, boolean admin) {
        Instant now = Instant.now();
        return Jwts.builder()
                .setSubject(userId.toString())
                .addClaims(Map.of("role", admin ? "ADMIN" : "USER"))
                .setIssuedAt(Date.from(now))
                .setExpiration(Date.from(now.plus(ttlHours, ChronoUnit.HOURS)))
                .signWith(key(), SignatureAlgorithm.HS256)
                .compact();
    }

    /** Field description. */
    public UUID parseUserId(String jwt) {
        String sub =
                Jwts.parserBuilder()
                        .setSigningKey(key())
                        .build()
                        .parseClaimsJws(jwt)
                        .getBody()
                        .getSubject();
        return UUID.fromString(sub);
    }
}
