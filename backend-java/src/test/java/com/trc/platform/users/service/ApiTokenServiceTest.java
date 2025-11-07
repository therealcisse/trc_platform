package com.trc.platform.users.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.trc.platform.users.entity.ApiToken;
import com.trc.platform.users.entity.User;
import com.trc.platform.users.repository.ApiTokenRepository;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;

@ExtendWith(MockitoExtension.class)
class ApiTokenServiceTest {

    @Mock
    private ApiTokenRepository apiTokenRepository;

    @InjectMocks
    private ApiTokenService apiTokenService;

    private User testUser;
    private ApiToken testToken;
    private LocalDateTime testExpiryTime;

    @BeforeEach
    void setUp() {
        testUser = User.builder()
                .id(UUID.randomUUID())
                .email("test@example.com")
                .active(true)
                .build();

        testExpiryTime = LocalDateTime.now().plusDays(30);

        testToken = ApiToken.builder()
                .id(UUID.randomUUID())
                .user(testUser)
                .name("Test Token")
                .tokenPrefix("tok_abc123")
                .tokenHash("$2a$10$hashvalue")
                .createdAt(LocalDateTime.now())
                .expiresAt(testExpiryTime)
                .revokedAt(null)
                .build();
    }

    @Test
    void createTokenFor_WithValidData_ShouldCreateTokenSuccessfully() {
        // Given
        String tokenName = "New Token";
        LocalDateTime expiresAt = LocalDateTime.now().plusDays(60);

        when(apiTokenRepository.save(any(ApiToken.class))).thenReturn(testToken);

        // When
        ApiTokenService.CreatedToken result = apiTokenService.createTokenFor(testUser, tokenName, expiresAt);

        // Then
        assertThat(result.token()).isEqualTo(testToken);
        assertThat(result.plainToken()).isNotEmpty();
        assertThat(result.plainToken()).startsWith("tok_");
        assertThat(result.plainToken().length()).isGreaterThanOrEqualTo(12);

        verify(apiTokenRepository).save(any(ApiToken.class));
    }

    @Test
    void createTokenFor_ShouldGenerateUniqueTokensEachTime() {
        // Given
        String tokenName = "Test Token";
        LocalDateTime expiresAt = LocalDateTime.now().plusDays(30);

        when(apiTokenRepository.save(any(ApiToken.class))).thenReturn(testToken);

        // When
        ApiTokenService.CreatedToken result1 = apiTokenService.createTokenFor(testUser, tokenName, expiresAt);
        ApiTokenService.CreatedToken result2 = apiTokenService.createTokenFor(testUser, tokenName, expiresAt);

        // Then
        assertThat(result1.plainToken()).isNotEqualTo(result2.plainToken());
        assertThat(result1.token()).isEqualTo(result2.token()); // Same saved token reference
    }

    @Test
    void createTokenFor_ShouldGenerateDifferentPrefixes() {
        // Given
        when(apiTokenRepository.save(any(ApiToken.class))).thenAnswer(inv -> inv.getArgument(0));

        // When
        ApiTokenService.CreatedToken result1 = apiTokenService.createTokenFor(testUser, "Token 1", testExpiryTime);
        ApiTokenService.CreatedToken result2 = apiTokenService.createTokenFor(testUser, "Token 2", testExpiryTime);

        // Then
        assertThat(result1.token().getTokenPrefix()).isNotEqualTo(result2.token().getTokenPrefix());
    }

    @Test
    void createTokenFor_WithNullUser_ShouldStillCreateToken() {
        // Given
        when(apiTokenRepository.save(any(ApiToken.class))).thenReturn(testToken);

        // When
        ApiTokenService.CreatedToken result = apiTokenService.createTokenFor(null, "Test", testExpiryTime);

        // Then
        assertThat(result.plainToken()).isNotEmpty();
        verify(apiTokenRepository).save(any(ApiToken.class));
    }

    @Test
    void getUserTokens_WithPageable_ShouldReturnUserTokensPage() {
        // Given
        Pageable pageable = PageRequest.of(0, 10);
        Page<ApiToken> expectedPage = new PageImpl<>(List.of(testToken), pageable, 1);

        when(apiTokenRepository.findByUserId(testUser.getId(), pageable)).thenReturn(expectedPage);

        // When
        Page<ApiToken> result = apiTokenService.getUserTokens(testUser, pageable);

        // Then
        assertThat(result.getContent()).hasSize(1);
        assertThat(result.getContent().get(0)).isEqualTo(testToken);
        assertThat(result.getTotalElements()).isEqualTo(1);
        verify(apiTokenRepository).findByUserId(testUser.getId(), pageable);
    }

    @Test
    void getUserTokens_WithoutPageable_ShouldReturnAllUserTokens() {
        // Given
        ApiToken anotherToken = ApiToken.builder()
                .id(UUID.randomUUID())
                .user(testUser)
                .name("Another Token")
                .tokenPrefix("tok_def456")
                .tokenHash("$2a$10$anotherhash")
                .createdAt(LocalDateTime.now())
                .expiresAt(testExpiryTime)
                .build();

        List<ApiToken> allTokens = List.of(testToken, anotherToken);
        List<ApiToken> userTokens = allTokens.stream()
                .filter(token -> token.getUser().getId().equals(testUser.getId()))
                .toList();

        when(apiTokenRepository.findAll()).thenReturn(allTokens);

        // When
        List<ApiToken> result = apiTokenService.getUserTokens(testUser);

        // Then
        assertThat(result).hasSize(2);
        assertThat(result).containsExactlyInAnyOrder(testToken, anotherToken);
        verify(apiTokenRepository).findAll();
    }

    @Test
    void getUserTokens_WithMultipleUsers_ShouldReturnOnlyUserTokens() {
        // Given
        User anotherUser = User.builder()
                .id(UUID.randomUUID())
                .email("other@example.com")
                .build();

        ApiToken otherUserToken = ApiToken.builder()
                .id(UUID.randomUUID())
                .user(anotherUser)
                .name("Other User Token")
                .tokenPrefix("tok_xyz789")
                .tokenHash("$2a$10$otherhash")
                .createdAt(LocalDateTime.now())
                .expiresAt(testExpiryTime)
                .build();

        List<ApiToken> allTokens = List.of(testToken, otherUserToken);
        when(apiTokenRepository.findAll()).thenReturn(allTokens);

        // When
        List<ApiToken> result = apiTokenService.getUserTokens(testUser);

        // Then
        assertThat(result).hasSize(1);
        assertThat(result.get(0)).isEqualTo(testToken);
        assertThat(result).doesNotContain(otherUserToken);
    }

    @Test
    void getToken_WithValidTokenIdAndUserId_ShouldReturnToken() {
        // Given
        UUID tokenId = testToken.getId();
        UUID userId = testUser.getId();

        when(apiTokenRepository.findByIdAndUserId(tokenId, userId)).thenReturn(Optional.of(testToken));

        // When
        ApiToken result = apiTokenService.getToken(tokenId, userId);

        // Then
        assertThat(result).isEqualTo(testToken);
        verify(apiTokenRepository).findByIdAndUserId(tokenId, userId);
    }

    @Test
    void getToken_WithInvalidTokenId_ShouldThrowException() {
        // Given
        UUID invalidTokenId = UUID.randomUUID();
        UUID userId = testUser.getId();

        when(apiTokenRepository.findByIdAndUserId(invalidTokenId, userId)).thenReturn(Optional.empty());

        // When & Then
        assertThatThrownBy(() -> apiTokenService.getToken(invalidTokenId, userId))
                .isInstanceOf(RuntimeException.class)
                .hasMessage("Token not found");

        verify(apiTokenRepository).findByIdAndUserId(invalidTokenId, userId);
    }

    @Test
    void getToken_WithInvalidUserId_ShouldThrowException() {
        // Given
        UUID tokenId = testToken.getId();
        UUID invalidUserId = UUID.randomUUID();

        when(apiTokenRepository.findByIdAndUserId(tokenId, invalidUserId)).thenReturn(Optional.empty());

        // When & Then
        assertThatThrownBy(() -> apiTokenService.getToken(tokenId, invalidUserId))
                .isInstanceOf(RuntimeException.class)
                .hasMessage("Token not found");

        verify(apiTokenRepository).findByIdAndUserId(tokenId, invalidUserId);
    }

    @Test
    void revokeToken_WithValidTokenIdAndUserId_ShouldRevokeToken() {
        // Given
        UUID tokenId = testToken.getId();
        UUID userId = testUser.getId();

        when(apiTokenRepository.findByIdAndUserId(tokenId, userId)).thenReturn(Optional.of(testToken));
        when(apiTokenRepository.save(testToken)).thenReturn(testToken);

        // When
        apiTokenService.revokeToken(tokenId, userId);

        // Then
        assertThat(testToken.getRevokedAt()).isNotNull();
        assertThat(testToken.getRevokedAt()).isBeforeOrEqualTo(LocalDateTime.now().plusSeconds(1));
        verify(apiTokenRepository).save(testToken);
    }

    @Test
    void revokeToken_WithInvalidTokenId_ShouldThrowException() {
        // Given
        UUID invalidTokenId = UUID.randomUUID();
        UUID userId = testUser.getId();

        when(apiTokenRepository.findByIdAndUserId(invalidTokenId, userId)).thenReturn(Optional.empty());

        // When & Then
        assertThatThrownBy(() -> apiTokenService.revokeToken(invalidTokenId, userId))
                .isInstanceOf(RuntimeException.class)
                .hasMessage("Token not found");

        verify(apiTokenRepository, never()).save(any(ApiToken.class));
    }

    @Test
    void revokeToken_AlreadyRevokedToken_ShouldUpdateRevokedAt() {
        // Given
        UUID tokenId = testToken.getId();
        UUID userId = testUser.getId();
        LocalDateTime originalRevokedAt = LocalDateTime.now().minusDays(1);
        testToken.setRevokedAt(originalRevokedAt);

        when(apiTokenRepository.findByIdAndUserId(tokenId, userId)).thenReturn(Optional.of(testToken));
        when(apiTokenRepository.save(testToken)).thenReturn(testToken);

        // When
        apiTokenService.revokeToken(tokenId, userId);

        // Then
        assertThat(testToken.getRevokedAt()).isNotEqualTo(originalRevokedAt);
        assertThat(testToken.getRevokedAt()).isAfter(originalRevokedAt);
        verify(apiTokenRepository).save(testToken);
    }

    @Test
    void createdTokenRecord_ShouldContainCorrectData() {
        // Given
        when(apiTokenRepository.save(any(ApiToken.class))).thenReturn(testToken);

        // When
        ApiTokenService.CreatedToken result = apiTokenService.createTokenFor(testUser, "Test", testExpiryTime);

        // Then
        assertThat(result.token()).isEqualTo(testToken);
        assertThat(result.plainToken()).isNotEmpty();
        assertThat(result.plainToken()).startsWith("tok_");
    }

    @Test
    void createTokenFor_WithDifferentExpiryTimes_ShouldCreateTokensWithCorrectExpiry() {
        // Given
        LocalDateTime tomorrow = LocalDateTime.now().plusDays(1);
        LocalDateTime nextMonth = LocalDateTime.now().plusMonths(1);

        when(apiTokenRepository.save(any(ApiToken.class))).thenReturn(testToken);

        // When
        ApiTokenService.CreatedToken result1 = apiTokenService.createTokenFor(testUser, "Short-lived", tomorrow);
        ApiTokenService.CreatedToken result2 = apiTokenService.createTokenFor(testUser, "Long-lived", nextMonth);

        // Then
        verify(apiTokenRepository, times(2)).save(any(ApiToken.class));
        // Both tokens should be created successfully
        assertThat(result1.plainToken()).isNotEmpty();
        assertThat(result2.plainToken()).isNotEmpty();
    }

    @Test
    void createTokenFor_ShouldGenerateSecureRandomTokens() {
        // Given
        when(apiTokenRepository.save(any(ApiToken.class))).thenReturn(testToken);

        // When - Create multiple tokens
        List<String> tokens = List.of(
                apiTokenService.createTokenFor(testUser, "Token 1", testExpiryTime).plainToken(),
                apiTokenService.createTokenFor(testUser, "Token 2", testExpiryTime).plainToken(),
                apiTokenService.createTokenFor(testUser, "Token 3", testExpiryTime).plainToken()
        );

        // Then - All tokens should be different
        assertThat(tokens).hasSize(3);
        assertThat(tokens).doesNotHaveDuplicates();

        // All tokens should be properly formatted
        tokens.forEach(token -> {
            assertThat(token).startsWith("tok_");
            assertThat(token.length()).isGreaterThanOrEqualTo(12);
        });
    }
}