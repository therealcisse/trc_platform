package com.trc.platform.core.service;

import com.trc.platform.config.Settings;
import com.trc.platform.config.SettingsService;
import com.trc.platform.core.dto.SolveResponse;
import com.trc.platform.usage.entity.BillingPeriod;
import com.trc.platform.usage.entity.RequestLog;
import com.trc.platform.usage.entity.RequestLog.RequestStatus;
import com.trc.platform.usage.repository.BillingPeriodRepository;
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
public class CoreProcessingServiceImpl implements CoreProcessingService {

    private final OpenAIClientService openAIClientService;

    private final SettingsService settingsService;

    private final BillingPeriodRepository billingRepo;

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

        int openaiMs = (int) (System.currentTimeMillis() - t1);
        int totalMs = (int) (System.currentTimeMillis() - t0);

        // naive request logging snippet
        RequestLog log =
                RequestLog.builder()
                        .user(user)
                        .requestTs(LocalDateTime.now())
                        .requestId(requestId)
                        .durationMs(totalMs)
                        .requestBytes(bytes.length)
                        .responseBytes(result != null ? result.length() : 0)
                        .status(
                                "ERROR".equals(result)
                                        ? RequestStatus.ERROR
                                        : RequestStatus.SUCCESS)
                        .result(result)
                        .build();

        // ensure current billing period exists
        billingRepo
                .findCurrentByUserId(user.getId())
                .ifPresentOrElse(
                        existing -> {},
                        () -> {
                            BillingPeriod bp =
                                    BillingPeriod.builder()
                                            .user(user)
                                            .periodStart(LocalDate.now().withDayOfMonth(1))
                                            .periodEnd(
                                                    LocalDate.now()
                                                            .withDayOfMonth(
                                                                    LocalDate.now()
                                                                            .lengthOfMonth()))
                                            .current(true)
                                            .build();
                            billingRepo.save(bp);
                        });

        int extractMs = 0; // placeholder for future image pre processing timing

        return SolveResponse.builder()
                .requestId(requestId.toString())
                .result(result)
                .durationMs(totalMs)
                .timings(
                        Map.of(
                                "extract_ms", extractMs,
                                "settings_ms", settingsMs,
                                "openai_ms", openaiMs,
                                "total_ms", totalMs))
                .build();
    }
}
