/* (C) 2025 */
package com.trc.platform.users.service;

import com.trc.platform.admin.entity.InviteCode;
import com.trc.platform.admin.repository.InviteCodeRepository;
import com.trc.platform.security.JwtService;
import com.trc.platform.users.dto.LoginRequest;
import com.trc.platform.users.dto.PasswordChangeRequest;
import com.trc.platform.users.dto.RegistrationRequest;
import com.trc.platform.users.entity.User;
import com.trc.platform.users.exception.EmailExistsException;
import com.trc.platform.users.exception.InvalidInviteCodeException;
import com.trc.platform.users.exception.PasswordMismatchException;
import com.trc.platform.users.exception.TermsNotAcceptedException;
import com.trc.platform.users.repository.UserRepository;
import jakarta.servlet.http.HttpServletRequest;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class AuthenticationService {

  private final UserRepository userRepository;
  private final InviteCodeRepository inviteCodeRepository;
  private final PasswordEncoder passwordEncoder;
  private final JwtService jwtService;
  private final EmailService emailService;

  @Transactional
  public void register(RegistrationRequest req, HttpServletRequest request) {
    // Validate email uniqueness (case-insensitive)
    validateEmail(req.getEmail());

    // Validate password confirmation
    validatePasswordConfirmation(req.getPassword(), req.getConfirmPassword());

    // Validate terms acceptance
    validateTermsAcceptance(req.getUserAcceptedTerms());

    // Validate and consume invite code
    InviteCode inviteCode = validateAndConsumeInviteCode(req.getInviteCode());

    // Create user
    User user =
        User.builder()
            .email(req.getEmail().toLowerCase())
            .passwordHash(passwordEncoder.encode(req.getPassword()))
            .userAcceptedTerms(Boolean.TRUE.equals(req.getUserAcceptedTerms()))
            .userAcknowledgedDisclaimer(Boolean.TRUE.equals(req.getUserAcknowledgedDisclaimer()))
            .dateJoined(LocalDateTime.now())
            .active(true)
            .staff(false)
            .build();
    user = userRepository.save(user);

    // Mark invite code as used
    inviteCode.markAsUsed(user);
    inviteCodeRepository.save(inviteCode);

    // Send verification email
    emailService.sendVerificationEmail(user.getEmail(), request);
  }

  private void validateEmail(String email) {
    userRepository
        .findByEmailIgnoreCase(email)
        .ifPresent(
            u -> {
              throw new EmailExistsException("Email already registered");
            });
  }

  private void validatePasswordConfirmation(String password, String confirmPassword) {
    if (!password.equals(confirmPassword)) {
      throw new PasswordMismatchException("Password confirmation does not match");
    }
  }

  private void validateTermsAcceptance(Boolean userAcceptedTerms) {
    if (!Boolean.TRUE.equals(userAcceptedTerms)) {
      throw new TermsNotAcceptedException("You must accept the terms to register");
    }
  }

  private InviteCode validateAndConsumeInviteCode(String code) {
    InviteCode inviteCode =
        inviteCodeRepository
            .findByCode(code)
            .orElseThrow(
                () -> new InvalidInviteCodeException("Invalid invite code", "invalid_invite"));

    if (!inviteCode.isValid()) {
      if (inviteCode.getUsedBy() != null) {
        throw new InvalidInviteCodeException("Invite code already used", "invite_used");
      } else if (inviteCode.isExpired()) {
        throw new InvalidInviteCodeException("Invite code has expired", "invite_expired");
      } else {
        throw new InvalidInviteCodeException("Invalid invite code", "invalid_invite");
      }
    }

    return inviteCode;
  }

  public Map<String, Object> login(LoginRequest req) {
    User user =
        userRepository
            .findByEmail(req.getEmail())
            .orElseThrow(() -> new IllegalArgumentException("Invalid credentials"));

    if (!passwordEncoder.matches(req.getPassword(), user.getPasswordHash())) {
      throw new IllegalArgumentException("Invalid credentials");
    }
    if (!Boolean.TRUE.equals(user.getActive())) {
      throw new IllegalArgumentException("Account is disabled");
    }

    String token =
        jwtService.generateSessionToken(user.getId(), Boolean.TRUE.equals(user.getStaff()));
    return Map.of(
        "id", user.getId().toString(),
        "email", user.getEmail(),
        "token", token);
  }

  public UUID getUserIdFromToken(String jwt) {
    return jwtService.parseUserId(jwt);
  }

  @Transactional
  public void changePassword(UUID userId, PasswordChangeRequest req) {
    // Hash password outside of transaction to avoid holding DB connections
    String hashedPassword = passwordEncoder.encode(req.getNewPassword());

    // Only the save operation needs to be transactional
    updatePasswordHash(userId, req, hashedPassword);
  }

  public void updatePasswordHash(UUID userId, PasswordChangeRequest req, String hashedPassword) {
    User user =
        userRepository
            .findById(userId)
            .orElseThrow(() -> new IllegalArgumentException("User not found"));

    // Validate current password
    if (!passwordEncoder.matches(req.getCurrentPassword(), user.getPasswordHash())) {
      throw new PasswordMismatchException("Current password is incorrect");
    }

    // Validate new password confirmation (assuming confirmPassword field exists)
    if (!req.getNewPassword().equals(req.getConfirmPassword())) {
      throw new PasswordMismatchException("New password confirmation does not match");
    }

    userRepository.updatePassword(userId, hashedPassword);
  }

  @Transactional
  public void verifyEmail(String token) {
    if (!emailService.validateVerificationToken(token)) {
      throw new IllegalArgumentException("Invalid or expired verification token");
    }

    String email = emailService.extractEmailFromToken(token);
    if (email == null) {
      throw new IllegalArgumentException("Invalid verification token");
    }

    User user =
        userRepository
            .findByEmailIgnoreCase(email)
            .orElseThrow(() -> new IllegalArgumentException("User not found"));

    // Check if user is already verified
    if (user.isEmailVerified()) {
      // User is already verified - do nothing (gracefully handle token reuse)
      return;
    }

    userRepository.verifyEmail(user.getId(), email, LocalDateTime.now());
  }

  public void resendVerificationEmail(String email, HttpServletRequest request) {
    User user =
        userRepository
            .findByEmailIgnoreCase(email)
            .orElseThrow(() -> new IllegalArgumentException("User not found"));

    if (user.isEmailVerified()) {
      throw new IllegalArgumentException("Email is already verified");
    }

    emailService.sendVerificationEmail(email, request);
  }

  public User findByEmail(String email) {
    return userRepository
        .findByEmailIgnoreCase(email)
        .orElseThrow(() -> new UsernameNotFoundException("User not found: " + email));
  }
}
