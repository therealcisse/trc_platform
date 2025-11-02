package com.trc.platform.core;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.trc.platform.security.JwtService;
import com.trc.platform.testsupport.PostgresIT;
import com.trc.platform.testsupport.TestDataFactory;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.context.ActiveProfiles;
// import org.springframework.test.context.Import;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
// @Import(MockOpenAIConfig.class)
class CoreSolveIntegrationTest extends PostgresIT {

    @Autowired MockMvc mvc;

    @Autowired ObjectMapper om;

    @Autowired TestDataFactory data;

    @Autowired JwtService jwt;

    @Test
    void solve_with_jwt_auth_returns_solve_response() throws Exception {
        var user = data.createUser("solver@example.com", false);
        var token = jwt.generateSessionToken(user.getId(), false);

        byte[] img = "fakepng".getBytes(StandardCharsets.UTF_8);
        MockMultipartFile file =
                new MockMultipartFile("image", "img.png", MediaType.IMAGE_PNG_VALUE, img);

        String resp =
                mvc.perform(
                                multipart("/api/core/solve")
                                        .file(file)
                                        .header("Authorization", "Bearer " + token))
                        .andExpect(status().isOk())
                        .andReturn()
                        .getResponse()
                        .getContentAsString();

        JsonNode root = om.readTree(resp).path("data");
        assertThat(root.path("requestId").asText()).isNotBlank();
        assertThat(root.path("result").asText()).isEqualTo("42");
        assertThat(root.path("durationMs").isInt()).isTrue();
        assertThat(root.path("timings").path("openai_ms").isInt()).isTrue();
    }
}
