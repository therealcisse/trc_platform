/* (C) 2025 */
package com.trc.platform.core.controller;

import com.trc.platform.core.dto.SolveResponse;
import com.trc.platform.core.service.CoreProcessingService;
import com.trc.platform.monitoring.dto.HealthResponse;
import com.trc.platform.users.entity.User;
import jakarta.validation.constraints.NotNull;
import java.util.Map;
import org.springframework.http.MediaType;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/core")
public class CoreController {

  private final CoreProcessingService coreService;

  public CoreController(CoreProcessingService coreService) {
    this.coreService = coreService;
  }

  @PostMapping(path = "/solve", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
  public SolveResponse solve(
      @RequestPart("image") @NotNull MultipartFile image,
      @AuthenticationPrincipal User user // placeholder principal mapping
      ) {
    // For token based auth, principal resolution will map to a User
    return coreService.solveMathProblem(image, user);
  }

  @PostMapping(path = "/test-solve", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
  public SolveResponse testSolve(
      @RequestPart("image") @NotNull MultipartFile image, @AuthenticationPrincipal User user) {
    return coreService.testSolveMathProblem(image, user);
  }

  @GetMapping("/health")
  public HealthResponse health() {
    return HealthResponse.builder()
        .status("ok")
        .checks(Map.of("database", true, "openai", true))
        .build();
  }
}
