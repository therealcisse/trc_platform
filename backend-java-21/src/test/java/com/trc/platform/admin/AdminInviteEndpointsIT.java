package com.trc.platform.admin;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
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

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
// @Import(MockOpenAIConfig.class)
class AdminInviteEndpointsIT extends PostgresIT {

    @Autowired MockMvc mvc;

    @Autowired ObjectMapper om;

    @Autowired TestDataFactory data;

    @Autowired JwtService jwt;

    private String adminAuth() {
        var admin = data.createUser("admin@example.com", true);
        return "Bearer " + jwt.generateSessionToken(admin.getId(), true);
    }

    @Test
    void create_list_deactivate_invite() throws Exception {
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
        String code = created.path("code").asText();
        assertThat(code).isNotBlank();

        String listResp =
                mvc.perform(get("/api/v1/admin/invites").header("Authorization", auth))
                        .andExpect(status().isOk())
                        .andReturn()
                        .getResponse()
                        .getContentAsString();
        assertThat(om.readTree(listResp).path("data").path("content").isArray()).isTrue();

        mvc.perform(
                        post("/api/v1/admin/invites/{code}/deactivate", code)
                                .header("Authorization", auth))
                .andExpect(status().isOk());

        mvc.perform(delete("/api/v1/admin/invites/expired").header("Authorization", auth))
                .andExpect(status().isOk());
    }
}
