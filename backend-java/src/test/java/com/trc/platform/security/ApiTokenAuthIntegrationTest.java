package com.trc.platform.security;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.trc.platform.testsupport.PostgresIT;
import com.trc.platform.testsupport.TestDataFactory;
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
class ApiTokenAuthIntegrationTest extends PostgresIT {

    @Autowired MockMvc mvc;

    @Autowired ObjectMapper om;

    @Autowired TestDataFactory data;

    @Test
    void solve_with_api_token_header_succeeds() throws Exception {
        var user = data.createUser("apitoken@example.com", false);
        var plain = "tok_test_123456789";
        data.createApiToken(user, plain);

        byte[] img = "fakepng".getBytes();
        MockMultipartFile file =
                new MockMultipartFile("file", "img.png", MediaType.IMAGE_PNG_VALUE, img);

        String resp =
                mvc.perform(multipart("/api/core/solve").file(file).header("X-API-Token", plain))
                        .andExpect(status().isOk())
                        .andReturn()
                        .getResponse()
                        .getContentAsString();

        JsonNode root = om.readTree(resp);
        assertThat(root.path("result").asText()).isEqualTo("42");
    }
}
