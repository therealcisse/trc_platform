/* (C) 2025 */
package com.trc.platform.usage.service;

import com.trc.platform.usage.dto.BillingPeriodDetailDto;
import com.trc.platform.usage.dto.BillingPeriodResponse;
import com.trc.platform.usage.dto.CurrentBillingResponse;
import com.trc.platform.usage.entity.BillingPeriod;
import com.trc.platform.usage.entity.RequestLog;
import com.trc.platform.usage.repository.BillingPeriodRepository;
import com.trc.platform.users.entity.User;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
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

  private static final int COST_PER_REQUEST_CENTS = 50;

  @Override
  @Transactional(readOnly = true)
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
  public List<BillingPeriodResponse> getBillingPeriodsList(User user) {
    Page<BillingPeriod> periods =
        billingPeriodRepository.findByUserIdOrderByPeriodStart(
            user.getId(), org.springframework.data.domain.PageRequest.of(0, 100));
    return periods.getContent().stream()
        .map(BillingPeriodResponse::fromEntity)
        .collect(Collectors.toList());
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

  @Override
  public BillingPeriod createOrUpdateCurrentBillingPeriod(User user) {
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

    BillingPeriod newPeriod =
        BillingPeriod.builder()
            .user(user)
            .periodStart(periodStart)
            .periodEnd(now.withDayOfMonth(now.lengthOfMonth()))
            .totalRequests(0)
            .totalCostCents(0)
            .current(true)
            .paymentStatus(BillingPeriod.PaymentStatus.pending)
            .build();

    return billingPeriodRepository.save(newPeriod);
  }

  @Override
  public void updateBillingPeriodCosts(UUID periodId) {
    Optional<BillingPeriod> periodOpt = billingPeriodRepository.findById(periodId);
    if (periodOpt.isEmpty()) {
      log.warn("Billing period not found for cost update: {}", periodId);
      return;
    }

    BillingPeriod period = periodOpt.get();
    Long requestCount = billingPeriodRepository.countRequestsByPeriodId(periodId);

    period.setTotalRequests(requestCount.intValue());
    period.setTotalCostCents(requestCount.intValue() * COST_PER_REQUEST_CENTS);

    billingPeriodRepository.save(period);
    log.debug(
        "Updated billing period {} costs: {} requests, {} cents",
        periodId,
        requestCount,
        period.getTotalCostCents());
  }

  private BillingPeriod getCurrentBillingPeriod(User user) {
    Optional<BillingPeriod> currentPeriodOpt =
        billingPeriodRepository.findCurrentByUserId(user.getId());

    if (currentPeriodOpt.isPresent()) {
      return currentPeriodOpt.get();
    }

    return createOrUpdateCurrentBillingPeriod(user);
  }

  private String formatPeriodLabel(LocalDate periodStart) {
    return periodStart.format(DateTimeFormatter.ofPattern("MMMM yyyy"));
  }
}
