package com.trc.platform.testsupport;

import com.trc.platform.core.service.OpenAIClientService;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import reactor.core.publisher.Mono;

@TestConfiguration
public class MockOpenAIConfig {

    @Bean
    public OpenAIClientService openAIClientService() {
        return new OpenAIClientService(null) {
            @Override
            public Mono<String> solveMathFromImage(
                    byte[] imageBytes, String model, int timeoutSeconds) {
                return Mono.just("42");
            }
        };
    }
}
