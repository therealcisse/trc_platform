package com.trc.platform.users.service;

import com.trc.platform.config.SettingsService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.stereotype.Service;

@Service
public class EmailVerificationService {

    /** Field description. */
    private final SettingsService settingsService;

    public EmailVerificationService(SettingsService settingsService) {
        this.settingsService = settingsService;
    }

    /** Field description. */
    public String buildVerificationUrl(String token, HttpServletRequest request) {
        return settingsService
                .getAppDomain()
                .map(domain -> domain + "/verify-email?token=" + token)
                .orElseGet(
                        () ->
                                request.getScheme()
                                        + "://"
                                        + request.getServerName()
                                        + "/verify-email?token="
                                        + token);
    }
}
