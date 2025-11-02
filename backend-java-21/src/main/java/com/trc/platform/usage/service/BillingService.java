package com.trc.platform.usage.service;

import com.trc.platform.usage.dto.BillingPeriodDetailDto;
import com.trc.platform.usage.dto.BillingPeriodResponse;
import com.trc.platform.usage.dto.CurrentBillingResponse;
import com.trc.platform.usage.entity.BillingPeriod;
import com.trc.platform.users.entity.User;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

public interface BillingService {
    BillingPeriod getCurrentBillingPeriod(User user);

    CurrentBillingResponse getCurrentBilling(User user);

    Page<BillingPeriod> getBillingPeriods(User user, Pageable pageable);

    Page<BillingPeriodResponse> getBillingPeriodsList(User user, int page, int size);

    BillingPeriodDetailDto getBillingPeriodDetail(User user, UUID periodId);
}
