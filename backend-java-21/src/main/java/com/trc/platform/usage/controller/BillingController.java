package com.trc.platform.usage.controller;

import com.trc.platform.security.UserPrincipal;
import com.trc.platform.usage.dto.BillingPeriodDetailDto;
import com.trc.platform.usage.dto.BillingPeriodResponse;
import com.trc.platform.usage.dto.CurrentBillingResponse;
import com.trc.platform.usage.dto.RequestLogResponse;
import com.trc.platform.usage.dto.UsageSummaryResponse;
import com.trc.platform.usage.service.BillingService;
import com.trc.platform.usage.service.UsageRequestsService;
import com.trc.platform.usage.service.UsageService;
import com.trc.platform.users.entity.User;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Sort;
import org.springframework.http.MediaType;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class BillingController {

    private final BillingService billingService;

    private final UsageService usageService;

    private final UsageRequestsService usageRequestsService;

    @GetMapping(value = "/billing/current", produces = MediaType.APPLICATION_JSON_VALUE)
    @ResponseBody
    public CurrentBillingResponse getOrCreateCurrentBilling(
            @AuthenticationPrincipal UserPrincipal userPrincipal) {
        if (userPrincipal == null) {
            throw new AccessDeniedException(
                    "Authentication required to access billing information");
        }
        User user = userPrincipal.getUser();
        return billingService.getCurrentBilling(user);
    }

    @GetMapping("/billing/periods")
    @ResponseBody
    public Page<BillingPeriodResponse> periods(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        if (userPrincipal == null) {
            throw new AccessDeniedException("Authentication required to access billing periods");
        }
        User user = userPrincipal.getUser();
        return billingService.getBillingPeriodsList(user, page, size);
    }

    @GetMapping("/billing/periods/{periodId}")
    @ResponseBody
    public BillingPeriodDetailDto detail(
            @PathVariable UUID periodId, @AuthenticationPrincipal UserPrincipal userPrincipal) {
        if (userPrincipal == null) {
            throw new AccessDeniedException(
                    "Authentication required to access billing period details");
        }
        User user = userPrincipal.getUser();
        return billingService.getBillingPeriodDetail(user, periodId);
    }

    @GetMapping("/usage/summary")
    @ResponseBody
    public UsageSummaryResponse summary(@AuthenticationPrincipal UserPrincipal userPrincipal) {
        if (userPrincipal == null) {
            throw new AccessDeniedException("Authentication required to access usage summary");
        }
        User user = userPrincipal.getUser();
        return usageService.getUsageSummary(user);
    }

    @GetMapping("/usage/requests")
    @ResponseBody
    public Page<RequestLogResponse> getUsageRequests(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            @RequestParam(required = false) String from,
            @RequestParam(required = false) String to,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "25") int size) {

        if (userPrincipal == null) {
            throw new AccessDeniedException("Authentication required to access usage requests");
        }
        User user = userPrincipal.getUser();
        Pageable pageable = PageRequest.of(page, size, Sort.by("requestTs").descending());
        return usageRequestsService.getUserRequests(user, from, to, pageable);
    }
}
