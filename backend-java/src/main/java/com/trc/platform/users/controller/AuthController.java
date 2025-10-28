/* (C) 2025 */
package com.trc.platform.users.controller;

import com.trc.platform.security.UserPrincipal;
import com.trc.platform.users.dto.*;
import com.trc.platform.users.service.AuthenticationService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class AuthController {

  private final AuthenticationService authenticationService;

  @PostMapping(value = "/customers/login", produces = MediaType.APPLICATION_JSON_VALUE)
  @ResponseBody
  public Map<String, Object> login(@Valid @RequestBody LoginRequest body) {
    return authenticationService.login(body);
  }

  @PostMapping("/customers/register")
  @ResponseStatus(HttpStatus.ACCEPTED)
  public void register(@Valid @RequestBody RegistrationRequest body, HttpServletRequest request) {
    authenticationService.register(body, request);
  }

  @PostMapping("/auth/password/change")
  public ResponseEntity<Void> changePassword(
      @Valid @RequestBody PasswordChangeRequest body,
      @AuthenticationPrincipal UserPrincipal userPrincipal) {
    if (userPrincipal == null) {
      return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
    }
    authenticationService.changePassword(userPrincipal.getId(), body);
    return ResponseEntity.ok().build();
  }

  @PostMapping("/auth/verify-email")
  public ResponseEntity<Void> verifyEmail(@Valid @RequestBody EmailVerificationRequest body) {
    authenticationService.verifyEmail(body.getToken());
    return ResponseEntity.ok().build();
  }

  @PostMapping("/auth/resend-verification")
  public ResponseEntity<Void> resendVerification(
      @Valid @RequestBody ResendVerificationRequest body, HttpServletRequest request) {
    authenticationService.resendVerificationEmail(body.getEmail(), request);
    return ResponseEntity.ok().build();
  }
}
