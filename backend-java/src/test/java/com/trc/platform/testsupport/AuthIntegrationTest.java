/* (C) 2025 */
package com.trc.platform.auth;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.trc.platform.testsupport.PostgresIT;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
// import org.springframework.test.context.Import;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
// @Import(MockOpenAIConfig.class)
class AuthIntegrationTest extends PostgresIT {

  @Autowired MockMvc mvc;
  @Autowired ObjectMapper om;

  @Test
  void register_and_login_returns_session_token() throws Exception {
    var regBody =
        """
{"email":"user1@example.com","password":"P@ssw0rd!","acceptedTerms":true,"acknowledgedDisclaimer":true}
""";
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
    assertThat(root.path("data").path("sessionToken").asText()).isNotBlank();
  }
}
