package com.trc.platform.core.controller;

import com.trc.platform.core.dto.SolveResponse;
import com.trc.platform.core.service.CoreProcessingService;
import com.trc.platform.monitoring.dto.HealthResponse;
import com.trc.platform.security.UserPrincipal;
import com.trc.platform.users.entity.User;
import jakarta.validation.constraints.NotNull;
import java.util.Map;
import org.springframework.http.MediaType;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/core")
public class CoreController {

    private final CoreProcessingService coreService;

    public CoreController(CoreProcessingService coreService) {
        this.coreService = coreService;
    }

    @PostMapping(
        path = "/solve",
        consumes = MediaType.MULTIPART_FORM_DATA_VALUE,
        produces = MediaType.APPLICATION_JSON_VALUE
    )
    @ResponseBody
    public SolveResponse solve(
            @RequestPart("file") @NotNull MultipartFile image,
            @AuthenticationPrincipal UserPrincipal userPrincipal) {
        if (userPrincipal == null) {
            throw new AccessDeniedException("Authentication required to access core solving functionality");
        }
        User user = userPrincipal.getUser();
        return coreService.solveMathProblem(image, user);
    }

    @PostMapping(path = "/test-solve", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @ResponseBody
    public SolveResponse testSolve(
            @RequestPart("file") @NotNull MultipartFile image,
            @AuthenticationPrincipal UserPrincipal userPrincipal) {
        if (userPrincipal == null) {
            throw new AccessDeniedException("Authentication required to access test solving functionality");
        }
        User user = userPrincipal.getUser();
        return coreService.testSolveMathProblem(image, user);
    }

    @GetMapping("/health")
    public HealthResponse health() {
        return new HealthResponse("ok", Map.of("database", true, "openai", true));
    }
}
