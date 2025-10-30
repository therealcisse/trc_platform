package com.trc.platform.core.controller;

import com.trc.platform.core.dto.SolveResponse;
import com.trc.platform.core.service.CoreProcessingService;
import com.trc.platform.monitoring.dto.HealthResponse;
import com.trc.platform.users.entity.User;
import jakarta.validation.constraints.NotNull;
import java.util.Map;
import org.springframework.http.MediaType;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/core")
public class CoreController {

    /** Field description. */
    private final CoreProcessingService coreService;

    public CoreController(CoreProcessingService coreService) {
        this.coreService = coreService;
    }

    @PostMapping(path = "/solve", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    /** Field description. */
    public SolveResponse solve(
            @RequestPart("image") @NotNull MultipartFile image,
            @AuthenticationPrincipal User user) { // placeholder principal mapping
        // For token based auth, principal resolution will map to a User
        return coreService.solveMathProblem(image, user);
    }

    @PostMapping(path = "/test-solve", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    /** Field description. */
    public SolveResponse testSolve(
            @RequestPart("image") @NotNull MultipartFile image,
            @AuthenticationPrincipal User user) {
        return coreService.testSolveMathProblem(image, user);
    }

    @GetMapping("/health")
    /** Field description. */
    public HealthResponse health() {
        return new HealthResponse(
                "ok",
                Map.of("database", true, "openai", true)
        );
    }
}
