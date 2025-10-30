package com.trc.platform.usage.service;

import com.trc.platform.usage.dto.BillingPeriodDetailDto;
import com.trc.platform.usage.dto.BillingPeriodResponse;
import com.trc.platform.usage.dto.CurrentBillingResponse;
import com.trc.platform.usage.entity.BillingPeriod;
import com.trc.platform.users.entity.User;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

public interface BillingService {

    CurrentBillingResponse getCurrentBilling(User user);

    Page<BillingPeriod> getBillingPeriods(User user, Pageable pageable);

    List<BillingPeriodResponse> getBillingPeriodsList(User user);

    BillingPeriodDetailDto getBillingPeriodDetail(User user, UUID periodId);

    BillingPeriod createOrUpdateCurrentBillingPeriod(User user);

    void updateBillingPeriodCosts(UUID periodId);
}
