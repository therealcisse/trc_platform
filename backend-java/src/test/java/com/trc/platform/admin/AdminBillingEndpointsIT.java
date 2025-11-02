package com.trc.platform.admin;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.trc.platform.security.JwtService;
import com.trc.platform.testsupport.PostgresIT;
import com.trc.platform.testsupport.TestDataFactory;
import com.trc.platform.usage.entity.BillingPeriod;
import com.trc.platform.usage.repository.BillingPeriodRepository;
import java.time.LocalDate;
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
class AdminBillingEndpointsIT extends PostgresIT {

    @Autowired MockMvc mvc;

    @Autowired ObjectMapper om;

    @Autowired TestDataFactory data;

    @Autowired JwtService jwt;

    @Autowired BillingPeriodRepository billingRepo;

    private String adminAuth() {
        var admin = data.createUser("admin2@example.com", true);
        return "Bearer " + jwt.generateSessionToken(admin.getId(), true);
    }

    @Test
    void mark_paid_overdue_waived_and_list() throws Exception {
        var user = data.createUser("billuser@example.com", false);
        BillingPeriod bp =
                BillingPeriod.builder()
                        .user(user)
                        .periodStart(LocalDate.now().withDayOfMonth(1))
                        .periodEnd(LocalDate.now().withDayOfMonth(LocalDate.now().lengthOfMonth()))
                        .current(true)
                        .paymentStatus(BillingPeriod.PaymentStatus.pending)
                        .totalCostCents(500)
                        .totalRequests(10)
                        .build();
        bp = billingRepo.save(bp);

        String auth = adminAuth();

        String paidResp =
                mvc.perform(
                                post("/api/v1/admin/billing/periods/{id}/mark-paid", bp.getId())
                                        .header("Authorization", auth)
                                        .contentType(MediaType.APPLICATION_JSON)
                                        .content(
                                                "{\"paidAmountCents\":500,\"paymentReference\":\"INV-1\"}"))
                        .andExpect(status().isOk())
                        .andReturn()
                        .getResponse()
                        .getContentAsString();
        assertThat(om.readTree(paidResp).path("data").path("paymentStatus").asText())
                .isEqualTo("PAID");

        String overdueResp =
                mvc.perform(
                                post("/api/v1/admin/billing/periods/{id}/mark-overdue", bp.getId())
                                        .header("Authorization", auth)
                                        .content("Late payment"))
                        .andExpect(status().isOk())
                        .andReturn()
                        .getResponse()
                        .getContentAsString();
        assertThat(om.readTree(overdueResp).path("data").path("paymentStatus").asText())
                .isEqualTo("OVERDUE");

        String waivedResp =
                mvc.perform(
                                post("/api/v1/admin/billing/periods/{id}/mark-waived", bp.getId())
                                        .header("Authorization", auth)
                                        .content("Waived by admin"))
                        .andExpect(status().isOk())
                        .andReturn()
                        .getResponse()
                        .getContentAsString();
        assertThat(om.readTree(waivedResp).path("data").path("paymentStatus").asText())
                .isEqualTo("WAIVED");

        String listResp =
                mvc.perform(get("/api/v1/admin/billing/periods").header("Authorization", auth))
                        .andExpect(status().isOk())
                        .andReturn()
                        .getResponse()
                        .getContentAsString();
        assertThat(om.readTree(listResp).path("data").path("content").isArray()).isTrue();
    }
}
