package com.trc.platform.core.service;

import java.time.Duration;
import java.util.Base64;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
public class OpenAIClientService {
    private static final String MATH_SOLVER_PROMPT =
    """
You are a mathematical problem solver. Your task is to:
1. Identify the mathematical problem or expression in the image
2. Solve it step by step
3. Return ONLY the final numerical answer

Rules:
- If the image contains a math problem, return only the numerical answer
- For expressions like "2+2", return "4"
- For equations like "x=5+3", return "8"
- If there are multiple problems, solve all and return answers separated by commas
- If you cannot identify a math problem, return "ERROR: No math problem found"
- Do not include units, explanations, or any other text - just the number(s)

Examples:
- Image shows "3 + 5" → Return: "8"
- Image shows "12 × 4" → Return: "48"
- Image shows "100 ÷ 5" → Return: "20"
- Image shows "7 - 3" → Return: "4"
- Image shows "2³" → Return: "8"
- Image shows "√16" → Return: "4"
- Image shows "What is 15% of 200?" → Return: "30"
- Image shows multiple: "2+2" and "3×3" → Return: "4, 9"
""";

    private final WebClient client;

    private static final ObjectMapper MAPPER = new ObjectMapper();

    @Value("${openai.api.key:}")
    private String apiKey;

    @Value("${openai.api.url:https://api.openai.com/v1/chat/completions}")
    private String apiUrl;

    public OpenAIClientService(WebClient openAiWebClient) {
        this.client = openAiWebClient;
    }

    public Mono<String> solveMathFromImage(byte[] imageBytes, String model, int timeoutSeconds) {
        String base64 = Base64.getEncoder().encodeToString(imageBytes);
        String payload = buildPayloadWithSchema(model, base64);

        return client.post()
        .uri(apiUrl)
        .header("Authorization", "Bearer " + apiKey)
        .contentType(MediaType.APPLICATION_JSON)
        .body(BodyInserters.fromValue(payload))
        .retrieve()
        // handle non-2xx statuses
        .onStatus(status -> status.is4xxClientError() || status.is5xxServerError(),
            clientResponse -> clientResponse
            .bodyToMono(String.class)  // read error body
            .flatMap(errorBody -> {
                log.error("OpenAI returned status {} with body: {}", clientResponse.statusCode(), errorBody);
                return Mono.error(new RuntimeException(
                    "OpenAI error: status=" + clientResponse.statusCode() + ", body=" + errorBody));
            })
        )
        // if status OK, parse body as String
        .bodyToMono(String.class)
        // optionally intercept other errors (e.g., connection timeout, parse errors)
        .onErrorResume(ex -> {
            log.error("Error calling OpenAI API", ex);
            return Mono.error(new RuntimeException("OpenAI API invocation failed", ex));
        })
        .timeout(Duration.ofSeconds(timeoutSeconds));
    }

    private String buildPayloadWithSchema(String model, String base64Image) {
        ObjectNode root = MAPPER.createObjectNode();
        root.put("model", model);

        ArrayNode messages = root.putArray("messages");
        // system message
        ObjectNode systemMsg = MAPPER.createObjectNode();
        systemMsg.put("role", "system");
        systemMsg.put("content", MATH_SOLVER_PROMPT);
        messages.add(systemMsg);

        // user message
        ObjectNode userMsg = MAPPER.createObjectNode();
        userMsg.put("role", "user");

        ArrayNode contentArray = userMsg.putArray("content");
        ObjectNode textNode = MAPPER.createObjectNode();
        textNode.put("type", "text");
        textNode.put("text", "Solve the math problem precisely and return the final answer only.");
        contentArray.add(textNode);

        ObjectNode imageNode = MAPPER.createObjectNode();
        imageNode.put("type", "image_url");
        ObjectNode imageUrlNode = MAPPER.createObjectNode();
        imageUrlNode.put("url", "data:image/png;base64," + base64Image);
        imageUrlNode.put("detail", "low");
        imageNode.set("image_url", imageUrlNode);
        contentArray.add(imageNode);

        userMsg.set("content", contentArray);
        messages.add(userMsg);

        // // Add the schema for Structured Outputs
        // ObjectNode responseFormat = MAPPER.createObjectNode();
        // responseFormat.put("type", "json_schema");
        // ObjectNode jsonSchema = MAPPER.createObjectNode();
        // jsonSchema.put("type", "object");
        // ObjectNode props = MAPPER.createObjectNode();
        // ObjectNode answerProp = MAPPER.createObjectNode();
        // answerProp.put("type", "string");
        // props.set("answer", answerProp);
        // jsonSchema.set("properties", props);
        // ArrayNode required = MAPPER.createArrayNode();
        // required.add("answer");
        // jsonSchema.set("required", required);
        // jsonSchema.put("additionalProperties", false);
        //
        // ObjectNode schemaWrapper = MAPPER.createObjectNode();
        // schemaWrapper.put("name", "math_result");
        // schemaWrapper.set("schema", jsonSchema);
        // schemaWrapper.put("strict", true);
        //
        // responseFormat.set("json_schema", schemaWrapper);
        //
        // root.set("response_format", responseFormat);

        root.put("temperature", 1);

        try {
            return MAPPER.writeValueAsString(root);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Failed to build OpenAI payload with schema", e);
        }
    }

   /**
     * Extracts the assistant’s answer from the OpenAI-style response JSON.
     * @param jsonResponse the full JSON string
     * @return the content of result.choices[0].message.content or null if missing
     * @throws RuntimeException if parsing fails
     */
    public static String extractAnswer(String jsonResponse) {
        try {
            JsonNode root = MAPPER.readTree(jsonResponse);
            JsonNode contentNode = root
                    .path("choices")
                    .path(0)
                    .path("message")
                    .path("content");

            if (contentNode.isMissingNode()) {
                return null;
            }
            return contentNode.asText();
        } catch (Exception e) {
            throw new RuntimeException("Failed to parse OpenAI response JSON", e);
        }
    }

}
