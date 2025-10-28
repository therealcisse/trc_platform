/* (C) 2025 */
package com.trc.platform.config;

import java.util.Arrays;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.filter.CorsFilter;

/**
 * Environment based CORS for frontend backend separation. Production must allow https app and admin
 * domains. Development allows localhost origins.
 */
@Configuration
public class CorsConfig {

  @Value("${cors.allowed-origins:}")
  private String allowedOriginsCsv;

  @Bean
  public CorsFilter corsFilter() {
    CorsConfiguration config = new CorsConfiguration();
    List<String> origins =
        allowedOriginsCsv == null || allowedOriginsCsv.isBlank()
            ? List.of("http://localhost:3000", "http://localhost:5173")
            : Arrays.stream(allowedOriginsCsv.split(",")).map(String::trim).toList();

    config.setAllowedOrigins(origins);
    config.setAllowCredentials(true);
    config.setAllowedMethods(
        List.of(
            HttpMethod.GET.name(),
            HttpMethod.POST.name(),
            HttpMethod.PUT.name(),
            HttpMethod.DELETE.name(),
            HttpMethod.PATCH.name(),
            HttpMethod.OPTIONS.name()));
    config.setAllowedHeaders(
        List.of("Authorization", "Content-Type", "X-CSRFToken", "X-Requested-With"));
    config.setMaxAge(3600L);

    UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/api/**", config);
    return new CorsFilter(source);
  }
}
