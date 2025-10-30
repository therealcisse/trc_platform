package com.trc.platform.users.controller;

import com.trc.platform.security.UserPrincipal;
import com.trc.platform.users.dto.EmailVerificationRequest;
import com.trc.platform.users.dto.LoginRequest;
import com.trc.platform.users.dto.PasswordChangeRequest;
import com.trc.platform.users.dto.RegistrationRequest;
import com.trc.platform.users.dto.ResendVerificationRequest;
import com.trc.platform.users.service.AuthenticationService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class AuthController {

    /** Field description. */
    private final AuthenticationService authenticationService;

    @PostMapping(value = "/customers/login", produces = MediaType.APPLICATION_JSON_VALUE)
    @ResponseBody
    /** Field description. */
    public Map<String, Object> login(@Valid @RequestBody LoginRequest body) {
        return authenticationService.login(body);
    }

    @PostMapping("/customers/register")
    @ResponseStatus(HttpStatus.ACCEPTED)
    /** Field description. */
    public void register(@Valid @RequestBody RegistrationRequest body, HttpServletRequest request) {
        authenticationService.register(body, request);
    }

    @PostMapping("/auth/password/change")
    /** Field description. */
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
    /** Field description. */
    public ResponseEntity<Void> verifyEmail(@Valid @RequestBody EmailVerificationRequest body) {
        authenticationService.verifyEmail(body.token());
        return ResponseEntity.ok().build();
    }

    @PostMapping("/auth/resend-verification")
    /** Field description. */
    public ResponseEntity<Void> resendVerification(
            @Valid @RequestBody ResendVerificationRequest body, HttpServletRequest request) {
        authenticationService.resendVerificationEmail(body.email(), request);
        return ResponseEntity.ok().build();
    }
}
