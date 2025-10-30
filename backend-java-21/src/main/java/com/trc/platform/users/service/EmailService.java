package com.trc.platform.users.service;

import com.trc.platform.config.SettingsService;
import jakarta.mail.internet.MimeMessage;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class EmailService {

    /** Field description. */
    private final JavaMailSender mailSender;

    /** Field description. */
    private final SettingsService settingsService;

    /** Field description. */
    private final EmailVerificationService emailVerificationService;

    /** Field description. */
    private final JwtEmailVerificationService jwtEmailVerificationService;

    @Value("${spring.mail.from:noreply@trc-platform.com}")
    /** Field description. */
    private String fromEmail;

    /** Field description. */
    public void sendVerificationEmail(String email, HttpServletRequest request) {
        try {
            String token = jwtEmailVerificationService.generateVerificationToken(email);
            String verificationUrl = emailVerificationService.buildVerificationUrl(token, request);

            String subject = "Verify your TRC Platform account";
            String htmlContent = buildVerificationEmailTemplate(verificationUrl);

            sendEmail(email, subject, htmlContent);
            log.info("JWT verification email sent to: {}", email);
        } catch (Exception e) {
            log.error("Failed to send JWT verification email to: {}", email, e);
            throw new RuntimeException("Failed to send verification email", e);
        }
    }

    /** Field description. */
    public void resendVerificationEmail(String email, HttpServletRequest request) {
        try {
            String token = jwtEmailVerificationService.generateVerificationToken(email);
            String verificationUrl = emailVerificationService.buildVerificationUrl(token, request);

            String subject = "Verify your TRC Platform account";
            String htmlContent = buildVerificationEmailTemplate(verificationUrl);

            sendEmail(email, subject, htmlContent);
            log.info("JWT verification email resent to: {}", email);
        } catch (Exception e) {
            log.error("Failed to resend JWT verification email to: {}", email, e);
            throw new RuntimeException("Failed to resend verification email", e);
        }
    }

    /** Field description. */
    public boolean validateVerificationToken(String token) {
        return jwtEmailVerificationService.validateVerificationToken(token);
    }

    /** Field description. */
    public String extractEmailFromToken(String token) {
        return jwtEmailVerificationService.extractEmailFromToken(token);
    }

    /** Field description. */
    private void sendEmail(String to, String subject, String htmlContent) {
        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");

            helper.setFrom(fromEmail);
            helper.setTo(to);
            helper.setSubject(subject);
            helper.setText(htmlContent, true);

            mailSender.send(message);
        } catch (Exception e) {
            log.error("Failed to send email to: {}", to, e);
            throw new RuntimeException("Failed to send email", e);
        }
    }

    /** Field description. */
    private String buildVerificationEmailTemplate(String verificationUrl) {
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Verify your TRC Platform account</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .button {
            display: inline-block;
            background-color: #007bff;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 4px;
            margin: 20px 0;
        }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to TRC Platform!</h1>
        </div>

        <p>Thank you for registering with TRC Platform. To complete your registration
        and activate your account, please verify your email address by clicking
        the button below:</p>

        <div style="text-align: center;">
            <a href="%s" class="button">Verify Email Address</a>
        </div>

        <p>If the button above doesn't work, you can copy and paste the following link into your browser:</p>
        <p style="word-break: break-all; background-color: #f5f5f5; padding: 10px; border-radius: 4px;">%s</p>

        <p><strong>Important:</strong> This verification link will expire in 24 hours for security reasons.</p>

        <p>If you didn't create an account with TRC Platform, please ignore this email.</p>

        <div class="footer">
            <p>This is an automated message from TRC Platform. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""
                .formatted(verificationUrl, verificationUrl);
    }
}
