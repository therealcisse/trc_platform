package com.trc.platform.usage.service;

import com.trc.platform.usage.entity.PaymentStatus;
import com.trc.platform.usage.dto.BillingPeriodDetailDto;
import com.trc.platform.usage.dto.BillingPeriodResponse;
import com.trc.platform.usage.dto.CurrentBillingResponse;
import com.trc.platform.usage.entity.BillingPeriod;
import com.trc.platform.usage.entity.RequestLog;
import com.trc.platform.usage.repository.BillingPeriodRepository;
import com.trc.platform.users.entity.User;
import com.trc.platform.users.repository.UserRepository;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.Map;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Slf4j
@Transactional
public class LiveBillingService implements BillingService {

    private final BillingPeriodRepository billingPeriodRepository;

    private final UserRepository userRepository;

    private static final int COST_PER_REQUEST_CENTS = 50;

    @Override
    @Transactional
    public CurrentBillingResponse getCurrentBilling(User user) {
        BillingPeriod currentPeriod = getCurrentBillingPeriod(user);

        return CurrentBillingResponse.builder()
                .id(currentPeriod.getId())
                .isCurrent(currentPeriod.getCurrent())
                .periodStart(currentPeriod.getPeriodStart())
                .periodEnd(currentPeriod.getPeriodEnd())
                .periodLabel(formatPeriodLabel(currentPeriod.getPeriodStart()))
                .paymentStatus(currentPeriod.getPaymentStatus().name())
                .totalRequests(currentPeriod.getTotalRequests())
                .totalCostCents(currentPeriod.getTotalCostCents())
                .build();
    }

    @Override
    @Transactional(readOnly = true)
    public Page<BillingPeriod> getBillingPeriods(User user, Pageable pageable) {
        return billingPeriodRepository.findByUserIdOrderByPeriodStart(user.getId(), pageable);
    }

    @Override
    @Transactional(readOnly = true)
    public Page<BillingPeriodResponse> getBillingPeriodsList(User user, int page, int size) {
        org.springframework.data.domain.Pageable pageable =
                org.springframework.data.domain.PageRequest.of(page, size);
        Page<BillingPeriod> periods = billingPeriodRepository.findByUserIdOrderByPeriodStart(user.getId(), pageable);

        Page<BillingPeriodResponse> results = periods
                .map(BillingPeriodResponse::fromEntity);

        return results;
    }

    @Override
    @Transactional(readOnly = true)
    public BillingPeriodDetailDto getBillingPeriodDetail(User user, UUID periodId) {
        Optional<BillingPeriod> periodOpt =
                billingPeriodRepository.findByUserIdAndId(user.getId(), periodId);
        if (periodOpt.isEmpty()) {
            throw new IllegalArgumentException("Billing period not found");
        }

        BillingPeriod period = periodOpt.get();
        List<RequestLog> requests = billingPeriodRepository.findRequestsByPeriodId(periodId);

        return BillingPeriodDetailDto.builder()
                .id(period.getId())
                .periodStart(period.getPeriodStart())
                .periodEnd(period.getPeriodEnd())
                .totalRequests(period.getTotalRequests())
                .totalCostCents(period.getTotalCostCents())
                .paymentStatus(period.getPaymentStatus())
                .current(period.getCurrent())
                .requests(
                        requests.stream()
                                .map(
                                        rl ->
                                                BillingPeriodDetailDto.RequestLogDto.builder()
                                                        .id(rl.getId())
                                                        .status(rl.getStatus().name())
                                                        .durationMs(rl.getDurationMs())
                                                        .flowId(rl.getFlowId())
                                                        .result(rl.getResult())
                                                        .build())
                                .toList())
                .build();
    }

    private BillingPeriod createOrUpdateCurrentBillingPeriod(User user) {
        if (user == null) {
            throw new IllegalArgumentException("User cannot be null");
        }

        LocalDate now = LocalDate.now();
        LocalDate periodStart = now.withDayOfMonth(1);

        Optional<BillingPeriod> existingPeriod =
                billingPeriodRepository.findByUserIdAndPeriodStart(user.getId(), periodStart);

        if (existingPeriod.isPresent()) {
            BillingPeriod period = existingPeriod.get();
            if (!period.getCurrent()) {
                period.setCurrent(true);
                return billingPeriodRepository.save(period);
            }
            return period;
        }

        // Get a fresh reference to the User entity to avoid lazy loading issues
        User freshUser = userRepository.findById(user.getId())
                .orElseThrow(() -> new IllegalArgumentException("User not found: " + user.getId()));

        BillingPeriod newPeriod =
                BillingPeriod.builder()
                        .user(freshUser)
                        .periodStart(periodStart)
                        .periodEnd(now.withDayOfMonth(now.lengthOfMonth()))
                        .totalRequests(0)
                        .totalCostCents(0)
                        .current(true)
                        .paymentStatus(PaymentStatus.pending)
                        .build();

        // Save the new period first
        BillingPeriod savedPeriod = billingPeriodRepository.save(newPeriod);

        // Mark all other periods as not current (excluding the new period)
        billingPeriodRepository.markAllOtherPeriodsNotCurrent(user.getId(), savedPeriod.getId());

        return savedPeriod;
    }

    private BillingPeriod getCurrentBillingPeriod(User user) {
        Optional<BillingPeriod> currentPeriodOpt =
                billingPeriodRepository.findCurrentByUserId(user.getId());

        return currentPeriodOpt.orElseGet(() -> createOrUpdateCurrentBillingPeriod(user));

    }

    private String formatPeriodLabel(LocalDate periodStart) {
        return periodStart.format(DateTimeFormatter.ofPattern("MMMM yyyy"));
    }
}
