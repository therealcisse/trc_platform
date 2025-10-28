/* (C) 2025 */
package com.trc.platform.core.service;

import java.time.Duration;
import java.util.Base64;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@Service
public class OpenAIClientService {

  private final WebClient client;

  @Value("${openai.api.key:}")
  private String apiKey;

  @Value("${openai.api.url:https://api.openai.com/v1/chat/completions}")
  private String apiUrl;

  public OpenAIClientService(WebClient openAiWebClient) {
    this.client = openAiWebClient;
  }

  public Mono<String> solveMathFromImage(byte[] imageBytes, String model, int timeoutSeconds) {
    String base64 = Base64.getEncoder().encodeToString(imageBytes);
    String payload =
        """
{
  "model": "%s",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Solve the math problem precisely and return the final answer only."},
        {"type": "input_image", "image_url": {"url": "data:image/png;base64,%s"}}
      ]
    }
  ],
  "temperature": 0.0
}"""
            .formatted(model, base64);

    return client
        .post()
        .uri(apiUrl)
        .header("Authorization", "Bearer " + apiKey)
        .contentType(MediaType.APPLICATION_JSON)
        .body(BodyInserters.fromValue(payload))
        .retrieve()
        .bodyToMono(String.class)
        .timeout(Duration.ofSeconds(timeoutSeconds));
  }
}
