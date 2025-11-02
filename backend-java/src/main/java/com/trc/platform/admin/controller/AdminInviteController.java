package com.trc.platform.admin.controller;

import com.trc.platform.admin.dto.CreateInviteCodeRequest;
import com.trc.platform.admin.dto.InviteCodeResponse;
import com.trc.platform.admin.service.AdminInviteService;
import com.trc.platform.security.UserPrincipal;
import com.trc.platform.users.entity.User;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.MediaType;
import org.springframework.security.access.prepost.PreAuthorize;
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
@RequestMapping("/api/v1/admin/invites")
@RequiredArgsConstructor
@PreAuthorize("hasRole('ADMIN')")
public class AdminInviteController {

    private final AdminInviteService service;

    @GetMapping
    public Page<InviteCodeResponse> list(
            @RequestParam(name = "page", defaultValue = "0") int page,
            @RequestParam(name = "size", defaultValue = "20") int size) {
        return service.list(PageRequest.of(page, size));
    }

    @PostMapping(produces = MediaType.APPLICATION_JSON_VALUE)
    public InviteCodeResponse create(
            @Valid @RequestBody CreateInviteCodeRequest req,
            @AuthenticationPrincipal UserPrincipal userPrincipal) {
        User user = userPrincipal.getUser();
        return service.create(req, user);
    }

    @PostMapping(value = "/{code}/activate", produces = MediaType.APPLICATION_JSON_VALUE)
    public InviteCodeResponse activate(@PathVariable String code) {
        return service.activate(code);
    }

    @PostMapping(value = "/{code}/deactivate", produces = MediaType.APPLICATION_JSON_VALUE)
    public InviteCodeResponse deactivate(@PathVariable String code) {
        return service.deactivate(code);
    }

    @DeleteMapping(value = "/expired")
    public void deleteExpired() {
        service.deleteExpired();
    }
}
