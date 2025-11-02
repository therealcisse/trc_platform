package com.trc.platform.admin.controller;

import com.trc.platform.admin.dto.BillingPeriodAdminResponse;
import com.trc.platform.admin.dto.MarkOverdueRequest;
import com.trc.platform.admin.dto.MarkPaidRequest;
import com.trc.platform.admin.dto.MarkWaivedRequest;
import com.trc.platform.admin.service.AdminBillingService;
import com.trc.platform.usage.entity.BillingPeriod;
import jakarta.validation.Valid;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/admin/billing/periods")
@RequiredArgsConstructor
@PreAuthorize("hasRole('ADMIN')")
public class AdminBillingController {

    private final AdminBillingService service;

    @GetMapping
    public Page<BillingPeriodAdminResponse> list(
            @RequestParam(required = false) UUID userId,
            @RequestParam(required = false) BillingPeriod.PaymentStatus status,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return service.list(userId, status, PageRequest.of(page, size));
    }

    @PostMapping("/{periodId}/mark-paid")
    public BillingPeriodAdminResponse markPaid(
            @PathVariable UUID periodId, @RequestBody @Valid MarkPaidRequest request) {
        return service.markPaid(periodId, request);
    }

    @PostMapping("/{periodId}/mark-overdue")
    public BillingPeriodAdminResponse markOverdue(
            @PathVariable UUID periodId, @RequestBody @Valid MarkOverdueRequest request) {
        return service.markOverdue(periodId, request);
    }

    @PostMapping("/{periodId}/mark-waived")
    public BillingPeriodAdminResponse markWaived(
            @PathVariable UUID periodId, @RequestBody @Valid MarkWaivedRequest request) {
        return service.markWaived(periodId, request);
    }
}
