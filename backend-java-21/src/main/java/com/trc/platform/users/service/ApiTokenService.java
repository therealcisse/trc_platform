package com.trc.platform.users.service;

import com.trc.platform.users.entity.ApiToken;
import com.trc.platform.users.entity.User;
import com.trc.platform.users.repository.ApiTokenRepository;
import java.time.LocalDateTime;
import java.util.Base64;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.crypto.bcrypt.BCrypt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ApiTokenService {

    private final ApiTokenRepository apiTokenRepository;

    public ApiTokenService(ApiTokenRepository apiTokenRepository) {
        this.apiTokenRepository = apiTokenRepository;
    }

    public record CreatedToken(ApiToken token, String plainToken) {}

    @Transactional
    public CreatedToken createTokenFor(User user, String name, LocalDateTime expiresAt) {
        byte[] bytes = new byte[32];
        new java.security.SecureRandom().nextBytes(bytes);
        String full = "tok_" + Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
        String prefix = full.substring(0, Math.min(12, full.length()));
        String hash = BCrypt.hashpw(full, BCrypt.gensalt());

        ApiToken token =
                ApiToken.builder()
                        .user(user)
                        .name(name)
                        .tokenPrefix(prefix)
                        .tokenHash(hash)
                        .createdAt(LocalDateTime.now())
                        .expiresAt(expiresAt)
                        .build();

        ApiToken savedToken = apiTokenRepository.save(token);
        return new CreatedToken(savedToken, full);
    }

    public List<ApiToken> getUserTokens(User user) {
        return apiTokenRepository.findAll().stream()
                .filter(token -> token.getUser().getId().equals(user.getId()))
                .toList();
    }

    public Page<ApiToken> getUserTokens(User user, Pageable pageable) {
        return apiTokenRepository.findByUserId(user.getId(), pageable);
    }

    public ApiToken getToken(UUID tokenId, UUID userId) {
        return apiTokenRepository
                .findByIdAndUserId(tokenId, userId)
                .orElseThrow(() -> new RuntimeException("Token not found"));
    }

    @Transactional
    public void revokeToken(UUID tokenId, UUID userId) {
        ApiToken token = getToken(tokenId, userId);
        token.setRevokedAt(LocalDateTime.now());
        apiTokenRepository.save(token);
    }
}
