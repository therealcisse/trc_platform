package com.trc.platform.core.service;

import com.trc.platform.config.Settings;
import com.trc.platform.config.SettingsService;
import com.trc.platform.core.dto.SolveResponse;
import com.trc.platform.usage.entity.BillingPeriod;
import com.trc.platform.usage.service.BillingService;
import com.trc.platform.usage.entity.RequestLog;
import com.trc.platform.usage.entity.RequestLog.RequestStatus;
import com.trc.platform.usage.repository.BillingPeriodRepository;
import com.trc.platform.usage.repository.RequestLogRepository;
import com.trc.platform.users.entity.User;
import java.io.IOException;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class LiveCoreProcessingService implements CoreProcessingService {

    private final OpenAIClientService openAIClientService;

    private final SettingsService settingsService;

    private final BillingService billingService;

    private final BillingPeriodRepository billingPeriodRepository;

    private final RequestLogRepository requestLogRepository;

    @Override
    public SolveResponse solveMathProblem(MultipartFile imageFile, User user) {
        return doSolve(imageFile, user, false);
    }

    @Override
    public SolveResponse testSolveMathProblem(MultipartFile imageFile, User user) {
        return doSolve(imageFile, user, true);
    }

    private SolveResponse doSolve(MultipartFile imageFile, User user, boolean test) {
        long t0 = System.currentTimeMillis();
        UUID requestId = UUID.randomUUID();
        int settingsMs = 0;

        Settings settings = settingsService.getSettings();
        String model = settings.getOpenaiModel();
        int timeout = settings.getOpenaiTimeoutSeconds();

        long t1 = System.currentTimeMillis();
        settingsMs = (int) (t1 - t0);

        byte[] bytes;
        try {
            bytes = imageFile.getBytes();
        } catch (IOException e) {
            throw new IllegalArgumentException("Invalid image");
        }

        String result =
                openAIClientService
                        .solveMathFromImage(bytes, model, timeout)
                        .onErrorResume(err -> Mono.just("ERROR"))
                        .block();

        String answer = OpenAIClientService.extractAnswer(result);

        int openaiMs = (int) (System.currentTimeMillis() - t1);
        int totalMs = (int) (System.currentTimeMillis() - t0);

        // Get current billing period using the billing service
        BillingPeriod currentBillingPeriod = billingService.getCurrentBillingPeriod(user);

        // Create request log associated with the billing period
        RequestLog log =
                RequestLog.builder()
                        .user(user)
                        .requestTs(LocalDateTime.now())
                        .requestId(requestId)
                        .durationMs(totalMs)
                        .requestBytes(bytes.length)
                        .responseBytes(result != null ? result.length() : 0)
                        .service(test ? "core.test_image_solve" : "core.image_solve")
                        .status(
                                "ERROR".equals(result)
                                        ? RequestStatus.ERROR
                                        : RequestStatus.SUCCESS)
                        .result(answer)
                        .billingPeriod(currentBillingPeriod)
                        .build();

        // Save the request log
        requestLogRepository.save(log);

        // Update billing period usage and cost
        Settings currentSettings = settingsService.getSettings();
        int costPerRequest = currentSettings.getCostPerRequestCents();

        // Increment billing period statistics
        currentBillingPeriod.setTotalRequests(currentBillingPeriod.getTotalRequests() + 1);
        currentBillingPeriod.setTotalCostCents(currentBillingPeriod.getTotalCostCents() + costPerRequest);

        // Save the updated billing period
        billingPeriodRepository.save(currentBillingPeriod);

        return SolveResponse.builder()
                .requestId(requestId.toString())
                .result(answer)
                .durationMs(totalMs)
                .timings(
                        Map.of(
                                "settings_ms", settingsMs,
                                "openai_ms", openaiMs,
                                "total_ms", totalMs))
                .build();
    }
}
