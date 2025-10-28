/* (C) 2025 */
package com.trc.platform.users.service;

import com.trc.platform.users.entity.ApiToken;
import com.trc.platform.users.entity.User;
import java.time.LocalDateTime;
import java.util.Base64;
import org.springframework.security.crypto.bcrypt.BCrypt;
import org.springframework.stereotype.Service;

@Service
public class ApiTokenService {

  public record CreatedToken(ApiToken token, String plainToken) {}

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

    return new CreatedToken(token, full);
  }
}
