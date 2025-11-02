package com.trc.platform.admin.service;

import com.trc.platform.admin.dto.CreateInviteCodeRequest;
import com.trc.platform.admin.dto.InviteCodeResponse;
import com.trc.platform.admin.entity.InviteCode;
import com.trc.platform.admin.repository.InviteCodeRepository;
import com.trc.platform.users.entity.User;
import jakarta.transaction.Transactional;
import java.security.SecureRandom;
import java.time.LocalDateTime;
import java.util.Base64;
import java.util.Locale;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
@RequiredArgsConstructor
public class AdminInviteService {

    private final InviteCodeRepository inviteCodeRepository;

    public Page<InviteCodeResponse> list(Pageable pageable) {
        Page<InviteCode> page = inviteCodeRepository.findAll(pageable);
        return page.map(this::toDto);
    }

    @Transactional
    public InviteCodeResponse create(CreateInviteCodeRequest req, User createdBy) {
        String code = StringUtils.hasText(req.code()) ? req.code() : generateCode();
        InviteCode ic =
                InviteCode.builder()
                        .code(code)
                        .active(true)
                        .expiresAt(req.expiresAt())
                        .createdAt(LocalDateTime.now())
                        .createdByUser(createdBy)
                        .build();
        return toDto(inviteCodeRepository.save(ic));
    }

    @Transactional
    public InviteCodeResponse activate(String code) {
        InviteCode ic =
                inviteCodeRepository
                        .findByCode(code)
                        .orElseThrow(() -> new IllegalArgumentException("Invite code not found"));
        ic.setActive(true);
        return toDto(inviteCodeRepository.save(ic));
    }

    @Transactional
    public InviteCodeResponse deactivate(String code) {
        InviteCode ic =
                inviteCodeRepository
                        .findByCode(code)
                        .orElseThrow(() -> new IllegalArgumentException("Invite code not found"));
        ic.setActive(false);
        return toDto(inviteCodeRepository.save(ic));
    }

    @Transactional
    public int deleteExpired() {
        return inviteCodeRepository.deleteExpiredCodes(LocalDateTime.now());
    }

    private InviteCodeResponse toDto(InviteCode ic) {
        return InviteCodeResponse.builder()
                .id(ic.getId())
                .code(ic.getCode())
                .active(ic.getActive())
                .createdAt(ic.getCreatedAt())
                .expiresAt(ic.getExpiresAt())
                .usedAt(ic.getUsedAt())
                .usedByUserId(ic.getUsedBy() != null ? ic.getUsedBy().getId() : null)
                .createdByUserId(
                        ic.getCreatedByUser() != null ? ic.getCreatedByUser().getId() : null)
                .createdByUserEmail(
                        ic.getCreatedByUser() != null ? ic.getCreatedByUser().getEmail() : null)
                .build();
    }

    private String generateCode() {
        byte[] buf = new byte[12];
        new SecureRandom().nextBytes(buf);
        String raw = Base64.getUrlEncoder().withoutPadding().encodeToString(buf);
        // remove non alnum to keep it user friendly
        return raw.replaceAll("[^A-Za-z0-9]", "").toLowerCase(Locale.ROOT);
    }
}
