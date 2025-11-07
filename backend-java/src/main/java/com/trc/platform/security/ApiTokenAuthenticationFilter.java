package com.trc.platform.security;

import com.trc.platform.users.entity.ApiToken;
import com.trc.platform.users.entity.User;
import com.trc.platform.users.repository.ApiTokenRepository;
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

    private final ApiTokenRepository apiTokenRepository;

    @Override
    protected void doFilterInternal(
            HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

        if (SecurityContextHolder.getContext().getAuthentication() == null) {
            String token = extractToken(request);
            if (token != null && token.startsWith("tok_")) {
                var tokenPrefix = token.length() > 12 ? token.substring(0, 12) : token;
                apiTokenRepository.findByTokenPrefix(tokenPrefix).ifPresent(this::authenticateWithToken);
            }
        }

        filterChain.doFilter(request, response);
    }

    @Transactional
    protected void authenticateWithToken(ApiToken apiToken) {
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

    private String extractToken(HttpServletRequest request) {
        String token = request.getHeader("X-Api-Token");
        if (StringUtils.hasText(token) && token.startsWith("tok_")) {
           return token;
        }

        String auth = request.getHeader(HttpHeaders.AUTHORIZATION);
        if (StringUtils.hasText(auth) && auth.startsWith("Bearer ")) {
            String bearer = auth.substring(7);
            return bearer;
        }
        return null;
    }
}
