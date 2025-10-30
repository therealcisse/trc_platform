package com.trc.platform.security;

import com.trc.platform.users.repository.ApiTokenRepository;
import com.trc.platform.users.repository.UserRepository;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.argon2.Argon2PasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableMethodSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    /** Field description. */
    private final JwtService jwtService;

    /** Field description. */
    private final UserRepository userRepository;

    /** Field description. */
    private final ApiTokenRepository apiTokenRepository;

    @Bean
    /** Field description. */
    public PasswordEncoder passwordEncoder() {
        return Argon2PasswordEncoder.defaultsForSpringSecurity_v5_8();
    }

    @Bean
    /** Field description. */
    public UserDetailsService userDetailsService(
            CustomUserDetailsService customUserDetailsService) {
        return customUserDetailsService;
    }

    @Bean
    /** Field description. */
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http.csrf(csrf -> csrf.disable())
                .sessionManagement(
                        sess -> sess.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(
                        auth ->
                                auth.requestMatchers(
                                                HttpMethod.POST,
                                                "/api/auth/**",
                                                "/api/customers/login",
                                                "/api/customers/register")
                                        .permitAll()
                                        .requestMatchers(
                                                HttpMethod.GET,
                                                "/actuator/health",
                                                "/v3/api-docs/**",
                                                "/swagger-ui/**")
                                        .permitAll()
                                        .requestMatchers(HttpMethod.GET, "/api/core/health")
                                        .permitAll()
                                        .requestMatchers("/api/v1/admin/**")
                                        .hasRole("ADMIN")
                                        .anyRequest()
                                        .authenticated())
                .exceptionHandling(
                        e ->
                                e.authenticationEntryPoint(
                                        (req, res, ex) ->
                                                res.sendError(
                                                        HttpServletResponse.SC_UNAUTHORIZED,
                                                        "Unauthorized")))
                .httpBasic(Customizer.withDefaults());

        http.addFilterBefore(
                new JwtAuthenticationFilter(jwtService, userRepository),
                org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter
                        .class);
        http.addFilterAfter(
                new ApiTokenAuthenticationFilter(apiTokenRepository, userRepository),
                JwtAuthenticationFilter.class);

        return http.build();
    }
}
