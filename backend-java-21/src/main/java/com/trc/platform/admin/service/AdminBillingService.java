package com.trc.platform.admin.service;

import com.trc.platform.admin.dto.BillingPeriodAdminResponse;
import com.trc.platform.admin.dto.MarkOverdueRequest;
import com.trc.platform.admin.dto.MarkPaidRequest;
import com.trc.platform.admin.dto.MarkWaivedRequest;
import com.trc.platform.usage.entity.BillingPeriod;
import com.trc.platform.usage.repository.BillingPeriodRepository;
import jakarta.transaction.Transactional;
import java.time.LocalDateTime;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class AdminBillingService {

    /** Field description. */
    private final BillingPeriodRepository billingRepo;

    /** Field description. */
    public Page<BillingPeriodAdminResponse> list(
            UUID userId, BillingPeriod.PaymentStatus status, Pageable pageable) {
        //    Page<BillingPeriod> page;
        //    if (userId != null && status != null) {
        //      page = billingRepo.findAll((root, q, cb) ->
        //          cb.and(
        //              cb.equal(root.get("user").get("id"), userId),
        //              cb.equal(root.get("paymentStatus"), status)
        //          ), pageable);
        //    } else if (userId != null) {
        //      page = billingRepo.findAll((root, q, cb) -> cb.equal(root.get("user").get("id"),
        // userId), pageable);
        //    } else if (status != null) {
        //      page = billingRepo.findAll((root, q, cb) -> cb.equal(root.get("paymentStatus"),
        // status),
        // pageable);
        //    } else {
        //      page = billingRepo.findAll(pageable);
        //    }
        //    return page.map(this::toDto);

        return null;
    }

    @Transactional
    /** Field description. */
    public BillingPeriodAdminResponse markPaid(UUID periodId, MarkPaidRequest request) {
        BillingPeriod bp =
                billingRepo
                        .findById(periodId)
                        .orElseThrow(
                                () -> new IllegalArgumentException("Billing period not found"));
        bp.setPaymentStatus(BillingPeriod.PaymentStatus.paid);
        bp.setPaidAt(request.paymentDate() != null ? request.paymentDate() : LocalDateTime.now());
        bp.setPaidAmountCents(request.paidAmountCents());
        bp.setPaymentReference(request.paymentReference());
        setNotesIfNotEmpty(bp, request.notes());
        return toDto(billingRepo.save(bp));
    }

    @Transactional
    /** Field description. */
    public BillingPeriodAdminResponse markOverdue(UUID periodId, MarkOverdueRequest request) {
        BillingPeriod bp =
                billingRepo
                        .findById(periodId)
                        .orElseThrow(
                                () -> new IllegalArgumentException("Billing period not found"));
        bp.setPaymentStatus(BillingPeriod.PaymentStatus.overdue);
        bp.setPaidAt(LocalDateTime.now());
        setNotesIfNotEmpty(bp, request.notes());
        // do not mutate paid fields for overdue
        return toDto(billingRepo.save(bp));
    }

    @Transactional
    /** Field description. */
    public BillingPeriodAdminResponse markWaived(UUID periodId, MarkWaivedRequest request) {
        BillingPeriod bp =
                billingRepo
                        .findById(periodId)
                        .orElseThrow(
                                () -> new IllegalArgumentException("Billing period not found"));
        bp.setPaymentStatus(BillingPeriod.PaymentStatus.waived);
        bp.setPaidAt(LocalDateTime.now());
        setNotesIfNotEmpty(bp, request.notes());
        return toDto(billingRepo.save(bp));
    }

    /** Field description. */
    private BillingPeriodAdminResponse toDto(BillingPeriod bp) {
        return BillingPeriodAdminResponse.builder()
                .id(bp.getId())
                .userId(bp.getUser().getId())
                .paymentStatus(bp.getPaymentStatus())
                .current(bp.getCurrent())
                .totalRequests(bp.getTotalRequests())
                .totalCostCents(bp.getTotalCostCents())
                .paidAt(bp.getPaidAt())
                .paidAmountCents(bp.getPaidAmountCents())
                .paymentReference(bp.getPaymentReference())
                .notes(bp.getNotes())
                .build();
    }

    /** Field description. */
    private void setNotesIfNotEmpty(BillingPeriod billingPeriod, String notes) {
        if (notes != null && !notes.trim().isEmpty()) {
            billingPeriod.setNotes(notes.trim());
        }
    }
}
