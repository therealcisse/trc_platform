package com.trc.platform.config;

import io.github.resilience4j.circuitbreaker.CircuitBreakerConfig;
import io.github.resilience4j.timelimiter.TimeLimiterConfig;
import java.time.Duration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.ExchangeStrategies;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class WebClientConfig {

    @Bean
    /** Field description. */
    public WebClient openAiWebClient() {
        // Large buffer to allow base64 images upload
        ExchangeStrategies strategies =
                ExchangeStrategies.builder()
                        .codecs(c -> c.defaultCodecs().maxInMemorySize(16 * 1024 * 1024))
                        .build();

        return WebClient.builder().exchangeStrategies(strategies).build();
    }

    @Bean
    /** Field description. */
    public CircuitBreakerConfig circuitBreakerConfig() {
        return CircuitBreakerConfig.custom()
                .failureRateThreshold(50)
                .slidingWindowSize(20)
                .waitDurationInOpenState(Duration.ofSeconds(10))
                .build();
    }

    @Bean
    /** Field description. */
    public TimeLimiterConfig timeLimiterConfig() {
        return TimeLimiterConfig.custom().timeoutDuration(Duration.ofSeconds(30)).build();
    }
}
