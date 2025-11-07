package com.trc.platform.security;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.Instant;
import java.util.Base64;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

@ExtendWith(MockitoExtension.class)
class JwtServiceTest {

    private JwtService jwtService;
    private String testSecret;
    private UUID testUserId;

    @BeforeEach
    void setUp() {
        jwtService = new JwtService();

        // Generate a proper Base64-encoded secret for testing
        byte[] secretBytes = new byte[64];
        new java.security.SecureRandom().nextBytes(secretBytes);
        testSecret = Base64.getEncoder().encodeToString(secretBytes);

        testUserId = UUID.randomUUID();

        // Set required fields using reflection
        ReflectionTestUtils.setField(jwtService, "base64Secret", testSecret);
        ReflectionTestUtils.setField(jwtService, "ttlHours", 24L);
    }

    @Test
    void generateSessionToken_WithValidData_ShouldGenerateToken() {
        // When
        String token = jwtService.generateSessionToken(testUserId, false);

        // Then
        assertThat(token).isNotEmpty();
        assertThat(token).contains(".");
        assertThat(token.split("\\.").length).isEqualTo(3); // Header.Payload.Signature
    }

    @Test
    void generateSessionToken_WithAdminUser_ShouldIncludeAdminRole() {
        // When
        String token = jwtService.generateSessionToken(testUserId, true);

        // Then
        assertThat(token).isNotEmpty();

        // Parse token to verify claims
        UUID parsedUserId = jwtService.parseUserId(token);
        assertThat(parsedUserId).isEqualTo(testUserId);
    }

    @Test
    void generateSessionToken_WithRegularUser_ShouldIncludeUserRole() {
        // When
        String token = jwtService.generateSessionToken(testUserId, false);

        // Then
        assertThat(token).isNotEmpty();

        // Parse token to verify claims
        UUID parsedUserId = jwtService.parseUserId(token);
        assertThat(parsedUserId).isEqualTo(testUserId);
    }

    @Test
    void parseUserId_WithValidToken_ShouldReturnUserId() {
        // Given
        String token = jwtService.generateSessionToken(testUserId, false);

        // When
        UUID parsedUserId = jwtService.parseUserId(token);

        // Then
        assertThat(parsedUserId).isEqualTo(testUserId);
    }

    @Test
    void parseUserId_WithDifferentUserToken_ShouldReturnCorrectUserId() {
        // Given
        UUID anotherUserId = UUID.randomUUID();
        String token = jwtService.generateSessionToken(anotherUserId, true);

        // When
        UUID parsedUserId = jwtService.parseUserId(token);

        // Then
        assertThat(parsedUserId).isEqualTo(anotherUserId);
    }

    @Test
    void parseUserId_WithExpiredToken_ShouldThrowException() {
        // Given - Create service with very short TTL
        JwtService shortLivedService = new JwtService();
        ReflectionTestUtils.setField(shortLivedService, "base64Secret", testSecret);
        ReflectionTestUtils.setField(shortLivedService, "ttlHours", -1L); // Expired

        String token = shortLivedService.generateSessionToken(testUserId, false);

        // When & Then
        assertThatThrownBy(() -> shortLivedService.parseUserId(token))
                .isInstanceOf(io.jsonwebtoken.ExpiredJwtException.class);
    }

    @Test
    void parseUserId_WithInvalidToken_ShouldThrowException() {
        // Given
        String invalidToken = "invalid.jwt.token";

        // When & Then
        assertThatThrownBy(() -> jwtService.parseUserId(invalidToken))
                .isInstanceOf(io.jsonwebtoken.MalformedJwtException.class);
    }

    @Test
    void parseUserId_WithWrongSecret_ShouldThrowException() {
        // Given
        String token = jwtService.generateSessionToken(testUserId, false);

        JwtService differentService = new JwtService();
        byte[] differentSecretBytes = new byte[64];
        new java.security.SecureRandom().nextBytes(differentSecretBytes);
        String differentSecret = Base64.getEncoder().encodeToString(differentSecretBytes);
        ReflectionTestUtils.setField(differentService, "base64Secret", differentSecret);
        ReflectionTestUtils.setField(differentService, "ttlHours", 24L);

        // When & Then
        assertThatThrownBy(() -> differentService.parseUserId(token))
                .isInstanceOf(io.jsonwebtoken.SignatureException.class);
    }

    @Test
    void parseUserId_WithMalformedToken_ShouldThrowException() {
        // Given
        String malformedToken = "not.a.jwt";

        // When & Then
        assertThatThrownBy(() -> jwtService.parseUserId(malformedToken))
                .isInstanceOf(io.jsonwebtoken.MalformedJwtException.class);
    }

    @Test
    void parseUserId_WithEmptyToken_ShouldThrowException() {
        // When & Then
        assertThatThrownBy(() -> jwtService.parseUserId(""))
                .isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void parseUserId_WithNullToken_ShouldThrowException() {
        // When & Then
        assertThatThrownBy(() -> jwtService.parseUserId(null))
                .isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void tokenGeneration_WithDifferentTTL_ShouldCreateTokensWithDifferentExpirationTimes() {
        // Given
        JwtService oneHourService = new JwtService();
        ReflectionTestUtils.setField(oneHourService, "base64Secret", testSecret);
        ReflectionTestUtils.setField(oneHourService, "ttlHours", 1L);

        JwtService twoHourService = new JwtService();
        ReflectionTestUtils.setField(twoHourService, "base64Secret", testSecret);
        ReflectionTestUtils.setField(twoHourService, "ttlHours", 2L);

        // When
        String oneHourToken = oneHourService.generateSessionToken(testUserId, false);
        String twoHourToken = twoHourService.generateSessionToken(testUserId, false);

        // Then
        assertThat(oneHourToken).isNotEqualTo(twoHourToken);

        // Both tokens should be valid for parsing
        UUID parsedFromOneHour = oneHourService.parseUserId(oneHourToken);
        UUID parsedFromTwoHour = twoHourService.parseUserId(twoHourToken);

        assertThat(parsedFromOneHour).isEqualTo(testUserId);
        assertThat(parsedFromTwoHour).isEqualTo(testUserId);
    }

    @Test
    void multipleTokenGeneration_ShouldCreateUniqueTokens() {
        // When
        String token1 = jwtService.generateSessionToken(testUserId, false);
        String token2 = jwtService.generateSessionToken(testUserId, false);

        // Then
        assertThat(token1).isNotEqualTo(token2);

        // Both tokens should parse to the same user ID
        UUID parsed1 = jwtService.parseUserId(token1);
        UUID parsed2 = jwtService.parseUserId(token2);

        assertThat(parsed1).isEqualTo(testUserId);
        assertThat(parsed2).isEqualTo(testUserId);
        assertThat(parsed1).isEqualTo(parsed2);
    }

    @Test
    void tokenWithInvalidBase64Secret_ShouldThrowExceptionDuringGeneration() {
        // Given
        JwtService invalidService = new JwtService();
        ReflectionTestUtils.setField(invalidService, "base64Secret", "invalid-base64");
        ReflectionTestUtils.setField(invalidService, "ttlHours", 24L);

        // When & Then
        assertThatThrownBy(() -> invalidService.generateSessionToken(testUserId, false))
                .isInstanceOf(io.jsonwebtoken.io.DecodingException.class);
    }
}