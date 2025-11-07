package com.trc.platform.testsupport;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.trc.platform.security.JwtService;
import com.trc.platform.testsupport.PostgresIT;
import com.trc.platform.testsupport.TestDataFactory;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
// import org.springframework.test.context.Import;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureMockMvc
@ActiveProfiles("test")
// @Import(MockOpenAIConfig.class)
class AuthIntegrationTest extends PostgresIT {

    @Autowired MockMvc mvc;

    @Autowired ObjectMapper om;

    @Autowired TestDataFactory data;

    @Autowired JwtService jwt;

    private String adminAuth() {
        var admin = data.createUser("admin@example.com", true);
        return "Bearer " + jwt.generateSessionToken(admin.getId(), true);
    }

    private String createInviteCode() throws Exception {
        String auth = adminAuth();

        String createResp =
                mvc.perform(
                                post("/api/v1/admin/invites")
                                        .header("Authorization", auth)
                                        .contentType(MediaType.APPLICATION_JSON)
                                        .content("{\"expiresAt\":null}"))
                        .andExpect(status().isOk())
                        .andReturn()
                        .getResponse()
                        .getContentAsString();

        JsonNode created = om.readTree(createResp).path("data");
        return created.path("code").asText();
    }

    @Test
    void register_and_login_returns_session_token() throws Exception {
        // Create invite code first
        String inviteCode = createInviteCode();

        var regBody =
                """
{"email":"user1@example.com","password":"P@ssw0rd!","userAcceptedTerms":true,"userAcknowledgedDisclaimer":true,"inviteCode":"%s"}
""".formatted(inviteCode);
        mvc.perform(
                        post("/api/customers/register")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(regBody))
                .andExpect(status().isCreated());

        var loginBody =
                """
                {"email":"user1@example.com","password":"P@ssw0rd!"}
                """;
        String resp =
                mvc.perform(
                                post("/api/customers/login")
                                        .contentType(MediaType.APPLICATION_JSON)
                                        .content(loginBody))
                        .andExpect(status().isOk())
                        .andReturn()
                        .getResponse()
                        .getContentAsString();

        JsonNode root = om.readTree(resp);
        assertThat(root.path("token").asText()).isNotBlank();
    }
}
