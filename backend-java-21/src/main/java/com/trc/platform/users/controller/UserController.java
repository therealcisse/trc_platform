package com.trc.platform.users.controller;

import com.trc.platform.security.UserPrincipal;
import com.trc.platform.users.dto.ApiTokenListResponse;
import com.trc.platform.users.dto.ApiTokenResponse;
import com.trc.platform.users.dto.CreateApiTokenRequest;
import com.trc.platform.users.entity.ApiToken;
import com.trc.platform.users.service.ApiTokenService;
import jakarta.validation.Valid;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/customers")
public class UserController {

    private final ApiTokenService apiTokenService;

    public UserController(ApiTokenService apiTokenService) {
        this.apiTokenService = apiTokenService;
    }

    @GetMapping(value = "/me", produces = MediaType.APPLICATION_JSON_VALUE)
    public Map<String, Object> me(@AuthenticationPrincipal UserPrincipal principal) {
        if (principal == null) {
            throw new org.springframework.security.authentication
                    .AuthenticationCredentialsNotFoundException("Authentication required");
        }
        var u = principal.getUser();
        Map<String, Object> data =
                Map.of(
                        "id", u.getId(),
                        "email", u.getEmail(),
                        "isEmailVerified", u.getEmailVerifiedAt() != null,
                        "userAcceptedTerms", u.getUserAcceptedTerms(),
                        "userAcknowledgedDisclaimer", u.getUserAcknowledgedDisclaimer(),
                        "dateJoined", u.getDateJoined());
        return data;
    }

    @PostMapping(value = "/tokens", produces = MediaType.APPLICATION_JSON_VALUE, consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<ApiTokenResponse> createToken(
            @AuthenticationPrincipal UserPrincipal principal,
            @Valid @RequestBody CreateApiTokenRequest request) {

        if (principal == null) {
            throw new org.springframework.security.authentication
                    .AuthenticationCredentialsNotFoundException(
                            "Authentication required");
        }

        var user = principal.getUser();
        var created = apiTokenService.createTokenFor(user, request.name(), request.expiresAt());
        var token = created.token();

        ApiTokenResponse response = new ApiTokenResponse(
                token.getId(),
                Optional.of(created.plainToken()),
                token.getName(),
                token.getCreatedAt(),
                token.getLastUsedAt(),
                token.getExpiresAt(),
                token.getRevokedAt(),
                token.getTokenPrefix()
        );

        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping(value = "/tokens", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Page<ApiTokenListResponse>> listTokens(
            @AuthenticationPrincipal UserPrincipal principal,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        if (principal == null) {
            throw new org.springframework.security.authentication
                    .AuthenticationCredentialsNotFoundException("Authentication required");
        }

        var user = principal.getUser();
        Pageable pageable = PageRequest.of(page, size);
        Page<ApiToken> tokens = apiTokenService.getUserTokens(user, pageable);

        Page<ApiTokenListResponse> responses = tokens.map(token -> new ApiTokenListResponse(
                token.getId(),
                token.getName(),
                token.getCreatedAt(),
                token.getLastUsedAt(),
                token.getExpiresAt(),
                token.getRevokedAt(),
                token.getTokenPrefix()
        ));

        return ResponseEntity.ok(responses);
    }

    @DeleteMapping(value = "/tokens/{tokenId}")
    public ResponseEntity<Void> revokeToken(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID tokenId) {

        if (principal == null) {
            throw new org.springframework.security.authentication
                    .AuthenticationCredentialsNotFoundException("Authentication required");
        }

        var user = principal.getUser();
        apiTokenService.revokeToken(tokenId, user.getId());

        return ResponseEntity.noContent().build();
    }
}
