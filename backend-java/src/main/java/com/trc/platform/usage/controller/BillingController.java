/* (C) 2025 */
package com.trc.platform.usage.controller;

import com.trc.platform.usage.dto.BillingPeriodDetailDto;
import com.trc.platform.usage.dto.BillingPeriodResponse;
import com.trc.platform.usage.dto.CurrentBillingResponse;
import com.trc.platform.usage.service.BillingService;
import com.trc.platform.users.entity.User;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class BillingController {

  private final BillingService billingService;

  @GetMapping("/billing/current")
  public CurrentBillingResponse current(@AuthenticationPrincipal User user) {
    return billingService.getCurrentBilling(user);
  }

  @GetMapping("/billing/periods")
  public Map<String, Object> periods(@AuthenticationPrincipal User user) {
    List<BillingPeriodResponse> results = billingService.getBillingPeriodsList(user);
    return Map.of("results", results);
  }

  @GetMapping("/billing/periods/{periodId}")
  public BillingPeriodDetailDto detail(
      @PathVariable UUID periodId, @AuthenticationPrincipal User user) {
    return billingService.getBillingPeriodDetail(user, periodId);
  }
}
