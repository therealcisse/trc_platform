package com.trc.platform.security;

import com.trc.platform.users.entity.ApiToken;
import com.trc.platform.users.entity.User;
import com.trc.platform.users.repository.ApiTokenRepository;
import com.trc.platform.users.repository.UserRepository;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.time.LocalDateTime;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

@Slf4j
@RequiredArgsConstructor
public class ApiTokenAuthenticationFilter extends OncePerRequestFilter {

    /** Field description. */
    private final ApiTokenRepository apiTokenRepository;

    /** Field description. */
    private final UserRepository userRepository;

    @Override
    /** Field description. */
    protected void doFilterInternal(
            HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

        if (SecurityContextHolder.getContext().getAuthentication() == null) {
            String token = extractToken(request);
            if (token != null && token.startsWith("tok_")) {
                // Find token by hash - the token itself is the hash
                apiTokenRepository.findByTokenHash(token).ifPresent(this::authenticateWithToken);
            }
        }

        filterChain.doFilter(request, response);
    }

    /** Field description. */
    @Transactional
    private void authenticateWithToken(ApiToken apiToken) {
        if (apiToken.getRevokedAt() != null) {
            return;
        }
        if (apiToken.getExpiresAt() != null
                && apiToken.getExpiresAt().isBefore(LocalDateTime.now())) {
            return;
        }

        User user = apiToken.getUser();
        apiToken.setLastUsedAt(LocalDateTime.now());
        apiTokenRepository.save(apiToken);

        UserPrincipal principal = new UserPrincipal(user);
        var authToken =
                new UsernamePasswordAuthenticationToken(
                        principal, null, principal.getAuthorities());
        SecurityContextHolder.getContext().setAuthentication(authToken);
    }

    /** Field description. */
    private String extractToken(HttpServletRequest request) {
        String auth = request.getHeader(HttpHeaders.AUTHORIZATION);
        if (StringUtils.hasText(auth) && auth.startsWith("Bearer ")) {
            String bearer = auth.substring(7);
            if (bearer.startsWith("tok_")) {
                return bearer;
            }
        }
        return null;
    }
}
