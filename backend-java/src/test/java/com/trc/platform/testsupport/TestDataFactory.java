package com.trc.platform.testsupport;

import com.trc.platform.users.entity.ApiToken;
import com.trc.platform.users.entity.User;
import com.trc.platform.users.repository.ApiTokenRepository;
import com.trc.platform.users.repository.UserRepository;
import java.time.LocalDateTime;
import org.springframework.security.crypto.bcrypt.BCrypt;
import org.springframework.stereotype.Component;

@Component
public class TestDataFactory {

    private final UserRepository userRepository;

    private final ApiTokenRepository apiTokenRepository;

    public TestDataFactory(UserRepository userRepository, ApiTokenRepository apiTokenRepository) {
        this.userRepository = userRepository;
        this.apiTokenRepository = apiTokenRepository;
    }

    public User createUser(String email, boolean admin) {
        User u =
                User.builder()
                        .email(email)
                        .passwordHash(BCrypt.hashpw("P@ssw0rd!", BCrypt.gensalt()))
                        .active(true)
                        .staff(admin)
                        .dateJoined(LocalDateTime.now())
                        .build();
        return userRepository.save(u);
    }

    public ApiToken createApiToken(User user, String plainToken) {
        ApiToken t =
                ApiToken.builder()
                        .user(user)
                        .name("test")
                        .tokenPrefix(plainToken.substring(0, Math.min(12, plainToken.length())))
                        .tokenHash(BCrypt.hashpw(plainToken, BCrypt.gensalt()))
                        .createdAt(LocalDateTime.now())
                        .build();
        return apiTokenRepository.save(t);
    }

    public String anyImagePngDataUrl() {
        // 1x1 transparent PNG
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGMAAQAABQAB";
    }
}
