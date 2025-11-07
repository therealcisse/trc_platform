package com.trc.platform.usage.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.trc.platform.usage.dto.BillingPeriodDetailDto;
import com.trc.platform.usage.dto.BillingPeriodResponse;
import com.trc.platform.usage.dto.CurrentBillingResponse;
import com.trc.platform.usage.entity.BillingPeriod;
import com.trc.platform.usage.entity.RequestLog;
import com.trc.platform.usage.repository.BillingPeriodRepository;
import com.trc.platform.users.entity.User;
import com.trc.platform.users.repository.UserRepository;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;

@ExtendWith(MockitoExtension.class)
class LiveBillingServiceTest {

    @Mock
    private BillingPeriodRepository billingPeriodRepository;

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private LiveBillingService billingService;

    private User testUser;
    private BillingPeriod testBillingPeriod;
    private RequestLog testRequestLog;
    private LocalDate testDate;

    @BeforeEach
    void setUp() {
        testDate = LocalDate.of(2024, 1, 15);

        testUser = User.builder()
                .id(UUID.randomUUID())
                .email("test@example.com")
                .active(true)
                .build();

        testBillingPeriod = BillingPeriod.builder()
                .id(UUID.randomUUID())
                .user(testUser)
                .periodStart(LocalDate.of(2024, 1, 1))
                .periodEnd(LocalDate.of(2024, 1, 31))
                .totalRequests(10)
                .totalCostCents(500) // 10 requests * 50 cents each
                .current(true)
                .paymentStatus(BillingPeriod.PaymentStatus.pending)
                .build();

        testRequestLog = RequestLog.builder()
                .id(UUID.randomUUID())
                .user(testUser)
                .requestTs(LocalDateTime.now())
                .requestId(UUID.randomUUID())
                .durationMs(1500)
                .service("core.image_solve")
                .status(RequestLog.RequestStatus.SUCCESS)
                .result("42")
                .billingPeriod(testBillingPeriod)
                .flowId("flow-123")
                .build();
    }

    @Test
    void getCurrentBilling_WithExistingPeriod_ShouldReturnCurrentBilling() {
        // Given
        when(billingPeriodRepository.findCurrentByUserId(testUser.getId()))
                .thenReturn(Optional.of(testBillingPeriod));

        // When
        CurrentBillingResponse result = billingService.getCurrentBilling(testUser);

        // Then
        assertThat(result.id()).isEqualTo(testBillingPeriod.getId());
        assertThat(result.isCurrent()).isTrue();
        assertThat(result.periodStart()).isEqualTo(testBillingPeriod.getPeriodStart());
        assertThat(result.periodEnd()).isEqualTo(testBillingPeriod.getPeriodEnd());
        assertThat(result.paymentStatus()).isEqualTo("pending");
        assertThat(result.totalRequests()).isEqualTo(10);
        assertThat(result.totalCostCents()).isEqualTo(500);
        assertThat(result.periodLabel()).isEqualTo("January 2024");
    }

    @Test
    void getCurrentBilling_WithNoExistingPeriod_ShouldCreateNewPeriod() {
        // Given
        when(billingPeriodRepository.findCurrentByUserId(testUser.getId()))
                .thenReturn(Optional.empty());
        when(userRepository.findById(testUser.getId())).thenReturn(Optional.of(testUser));
        when(billingPeriodRepository.save(any(BillingPeriod.class))).thenReturn(testBillingPeriod);

        // When
        CurrentBillingResponse result = billingService.getCurrentBilling(testUser);

        // Then
        assertThat(result.id()).isEqualTo(testBillingPeriod.getId());
        assertThat(result.isCurrent()).isTrue();
        verify(billingPeriodRepository).save(any(BillingPeriod.class));
        verify(billingPeriodRepository).markAllOtherPeriodsNotCurrent(testUser.getId(), testBillingPeriod.getId());
    }

    @Test
    void getCurrentBilling_WithNullUser_ShouldThrowException() {
        // When & Then
        assertThatThrownBy(() -> billingService.getCurrentBilling(null))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("User cannot be null");
    }

    @Test
    void getCurrentBillingPeriod_WithExistingCurrentPeriod_ShouldReturnPeriod() {
        // Given
        when(billingPeriodRepository.findCurrentByUserId(testUser.getId()))
                .thenReturn(Optional.of(testBillingPeriod));

        // When
        BillingPeriod result = billingService.getCurrentBillingPeriod(testUser);

        // Then
        assertThat(result).isEqualTo(testBillingPeriod);
        verify(billingPeriodRepository, never()).save(any(BillingPeriod.class));
    }

    @Test
    void getCurrentBillingPeriod_WithNoCurrentPeriod_ShouldCreateNewPeriod() {
        // Given
        when(billingPeriodRepository.findCurrentByUserId(testUser.getId()))
                .thenReturn(Optional.empty());
        when(userRepository.findById(testUser.getId())).thenReturn(Optional.of(testUser));
        when(billingPeriodRepository.save(any(BillingPeriod.class))).thenReturn(testBillingPeriod);

        // When
        BillingPeriod result = billingService.getCurrentBillingPeriod(testUser);

        // Then
        assertThat(result).isEqualTo(testBillingPeriod);
        verify(billingPeriodRepository).save(any(BillingPeriod.class));
        verify(billingPeriodRepository).markAllOtherPeriodsNotCurrent(testUser.getId(), testBillingPeriod.getId());
    }

    @Test
    void getBillingPeriods_WithValidUser_ShouldReturnPageOfPeriods() {
        // Given
        Pageable pageable = PageRequest.of(0, 10);
        Page<BillingPeriod> expectedPage = new PageImpl<>(List.of(testBillingPeriod), pageable, 1);

        when(billingPeriodRepository.findByUserIdOrderByPeriodStart(testUser.getId(), pageable))
                .thenReturn(expectedPage);

        // When
        Page<BillingPeriod> result = billingService.getBillingPeriods(testUser, pageable);

        // Then
        assertThat(result.getContent()).hasSize(1);
        assertThat(result.getContent().get(0)).isEqualTo(testBillingPeriod);
        assertThat(result.getTotalElements()).isEqualTo(1);
    }

    @Test
    void getBillingPeriodsList_WithValidUser_ShouldReturnPageOfResponses() {
        // Given
        Pageable pageable = PageRequest.of(0, 10);
        Page<BillingPeriod> expectedPage = new PageImpl<>(List.of(testBillingPeriod), pageable, 1);

        when(billingPeriodRepository.findByUserIdOrderByPeriodStart(testUser.getId(), pageable))
                .thenReturn(expectedPage);

        // When
        Page<BillingPeriodResponse> result = billingService.getBillingPeriodsList(testUser, 0, 10);

        // Then
        assertThat(result.getContent()).hasSize(1);
        BillingPeriodResponse response = result.getContent().get(0);
        assertThat(response.id()).isEqualTo(testBillingPeriod.getId());
        assertThat(response.periodStart()).isEqualTo(testBillingPeriod.getPeriodStart());
        assertThat(response.periodEnd()).isEqualTo(testBillingPeriod.getPeriodEnd());
        assertThat(response.totalRequests()).isEqualTo(testBillingPeriod.getTotalRequests());
        assertThat(response.totalCostCents()).isEqualTo(testBillingPeriod.getTotalCostCents());
        assertThat(response.paymentStatus()).isEqualTo(testBillingPeriod.getPaymentStatus().name());
        assertThat(response.isCurrent()).isEqualTo(testBillingPeriod.getCurrent());
    }

    @Test
    void getBillingPeriodDetail_WithValidPeriod_ShouldReturnDetail() {
        // Given
        UUID periodId = testBillingPeriod.getId();
        List<RequestLog> requests = List.of(testRequestLog);

        when(billingPeriodRepository.findByUserIdAndId(testUser.getId(), periodId))
                .thenReturn(Optional.of(testBillingPeriod));
        when(billingPeriodRepository.findRequestsByPeriodId(periodId))
                .thenReturn(requests);

        // When
        BillingPeriodDetailDto result = billingService.getBillingPeriodDetail(testUser, periodId);

        // Then
        assertThat(result.id()).isEqualTo(testBillingPeriod.getId());
        assertThat(result.periodStart()).isEqualTo(testBillingPeriod.getPeriodStart());
        assertThat(result.periodEnd()).isEqualTo(testBillingPeriod.getPeriodEnd());
        assertThat(result.totalRequests()).isEqualTo(testBillingPeriod.getTotalRequests());
        assertThat(result.totalCostCents()).isEqualTo(testBillingPeriod.getTotalCostCents());
        assertThat(result.paymentStatus()).isEqualTo(testBillingPeriod.getPaymentStatus());
        assertThat(result.current()).isEqualTo(testBillingPeriod.getCurrent());

        assertThat(result.requests()).hasSize(1);
        BillingPeriodDetailDto.RequestLogDto requestDto = result.requests().get(0);
        assertThat(requestDto.id()).isEqualTo(testRequestLog.getId());
        assertThat(requestDto.status()).isEqualTo("SUCCESS");
        assertThat(requestDto.durationMs()).isEqualTo(testRequestLog.getDurationMs());
        assertThat(requestDto.flowId()).isEqualTo(testRequestLog.getFlowId());
        assertThat(requestDto.result()).isEqualTo(testRequestLog.getResult());
    }

    @Test
    void getBillingPeriodDetail_WithInvalidPeriodId_ShouldThrowException() {
        // Given
        UUID invalidPeriodId = UUID.randomUUID();

        when(billingPeriodRepository.findByUserIdAndId(testUser.getId(), invalidPeriodId))
                .thenReturn(Optional.empty());

        // When & Then
        assertThatThrownBy(() -> billingService.getBillingPeriodDetail(testUser, invalidPeriodId))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Billing period not found");
    }

    
    @Test
    void formatPeriodLabel_WithDifferentDates_ShouldReturnCorrectFormat() {
        // When & Then - This tests private method through public method
        when(billingPeriodRepository.findCurrentByUserId(testUser.getId()))
                .thenReturn(Optional.of(testBillingPeriod));

        CurrentBillingResponse result = billingService.getCurrentBilling(testUser);
        assertThat(result.periodLabel()).isEqualTo("January 2024");
    }

    @Test
    void billingPeriodsWithDifferentPaymentStatuses_ShouldReturnCorrectStatus() {
        // Given
        testBillingPeriod.setPaymentStatus(BillingPeriod.PaymentStatus.paid);
        testBillingPeriod.setPaidAt(LocalDateTime.now());
        testBillingPeriod.setPaidAmountCents(500);

        when(billingPeriodRepository.findCurrentByUserId(testUser.getId()))
                .thenReturn(Optional.of(testBillingPeriod));

        // When
        CurrentBillingResponse result = billingService.getCurrentBilling(testUser);

        // Then
        assertThat(result.paymentStatus()).isEqualTo("paid");
    }

    @Test
    void billingPeriodWithZeroRequests_ShouldReturnZeroCost() {
        // Given
        testBillingPeriod.setTotalRequests(0);
        testBillingPeriod.setTotalCostCents(0);

        when(billingPeriodRepository.findCurrentByUserId(testUser.getId()))
                .thenReturn(Optional.of(testBillingPeriod));

        // When
        CurrentBillingResponse result = billingService.getCurrentBilling(testUser);

        // Then
        assertThat(result.totalRequests()).isEqualTo(0);
        assertThat(result.totalCostCents()).isEqualTo(0);
    }
}