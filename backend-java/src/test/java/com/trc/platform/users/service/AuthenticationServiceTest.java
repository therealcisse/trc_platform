package com.trc.platform.users.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.trc.platform.admin.entity.InviteCode;
import com.trc.platform.admin.repository.InviteCodeRepository;
import com.trc.platform.users.dto.LoginRequest;
import com.trc.platform.users.dto.PasswordChangeRequest;
import com.trc.platform.users.dto.RegistrationRequest;
import com.trc.platform.users.entity.User;
import com.trc.platform.users.exception.EmailExistsException;
import com.trc.platform.users.exception.InvalidInviteCodeException;
import com.trc.platform.users.exception.PasswordMismatchException;
import com.trc.platform.users.exception.TermsNotAcceptedException;
import com.trc.platform.users.repository.UserRepository;
import com.trc.platform.security.JwtService;
import jakarta.servlet.http.HttpServletRequest;
import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

@ExtendWith(MockitoExtension.class)
class AuthenticationServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private InviteCodeRepository inviteCodeRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @Mock
    private JwtService jwtService;

    @Mock
    private EmailService emailService;

    @Mock
    private HttpServletRequest request;

    @InjectMocks
    private AuthenticationService authenticationService;

    private User testUser;
    private InviteCode testInviteCode;

    @BeforeEach
    void setUp() {
        testUser = User.builder()
                .id(UUID.randomUUID())
                .email("test@example.com")
                .passwordHash("hashedPassword")
                .active(true)
                .staff(false)
                .emailVerifiedAt(null)
                .build();

        testInviteCode = InviteCode.builder()
                .id(UUID.randomUUID())
                .code("TEST123")
                .active(true)
                .usedBy(null)
                .createdAt(LocalDateTime.now())
                .expiresAt(LocalDateTime.now().plusDays(30))
                .build();
    }

    @Test
    void register_WithValidData_ShouldCreateUserSuccessfully() {
        // Given
        RegistrationRequest registrationRequest = new RegistrationRequest(
                "test@example.com",
                "password123",
                "password123",
                "TEST123",
                true,
                true
        );

        when(userRepository.findByEmailIgnoreCase("test@example.com")).thenReturn(Optional.empty());
        when(inviteCodeRepository.findByCode("TEST123")).thenReturn(Optional.of(testInviteCode));
        when(passwordEncoder.encode("password123")).thenReturn("hashedPassword");
        when(userRepository.save(any(User.class))).thenReturn(testUser);
        when(inviteCodeRepository.save(any(InviteCode.class))).thenReturn(testInviteCode);

        // When
        authenticationService.register(registrationRequest, request);

        // Then
        verify(userRepository).save(any(User.class));
        verify(emailService).sendVerificationEmail("test@example.com", request);
        assertThat(testInviteCode.getUsedBy()).isEqualTo(testUser);
    }

    @Test
    void register_WithExistingEmail_ShouldThrowEmailExistsException() {
        // Given
        RegistrationRequest registrationRequest = new RegistrationRequest(
                "test@example.com",
                "password123",
                "password123",
                "TEST123",
                true,
                true
        );

        when(userRepository.findByEmailIgnoreCase("test@example.com")).thenReturn(Optional.of(testUser));

        // When & Then
        assertThatThrownBy(() -> authenticationService.register(registrationRequest, request))
                .isInstanceOf(EmailExistsException.class)
                .hasMessage("Email already registered");

        verify(userRepository, never()).save(any(User.class));
        verify(emailService, never()).sendVerificationEmail(anyString(), any());
    }

    @Test
    void register_WithPasswordMismatch_ShouldThrowPasswordMismatchException() {
        // Given
        RegistrationRequest registrationRequest = new RegistrationRequest(
                "test@example.com",
                "password123",
                "differentpassword",
                "TEST123",
                true,
                true
        );

        when(userRepository.findByEmailIgnoreCase("test@example.com")).thenReturn(Optional.empty());

        // When & Then
        assertThatThrownBy(() -> authenticationService.register(registrationRequest, request))
                .isInstanceOf(PasswordMismatchException.class)
                .hasMessage("Password confirmation does not match");

        verify(userRepository, never()).save(any(User.class));
        verify(emailService, never()).sendVerificationEmail(anyString(), any());
    }

    @Test
    void register_WithTermsNotAccepted_ShouldThrowTermsNotAcceptedException() {
        // Given
        RegistrationRequest registrationRequest = new RegistrationRequest(
                "test@example.com",
                "password123",
                "password123",
                "TEST123",
                false,
                true
        );

        when(userRepository.findByEmailIgnoreCase("test@example.com")).thenReturn(Optional.empty());

        // When & Then
        assertThatThrownBy(() -> authenticationService.register(registrationRequest, request))
                .isInstanceOf(TermsNotAcceptedException.class)
                .hasMessage("You must accept the terms to register");

        verify(userRepository, never()).save(any(User.class));
        verify(emailService, never()).sendVerificationEmail(anyString(), any());
    }

    @Test
    void register_WithInvalidInviteCode_ShouldThrowInvalidInviteCodeException() {
        // Given
        RegistrationRequest registrationRequest = new RegistrationRequest(
                "test@example.com",
                "password123",
                "password123",
                "INVALID",
                true,
                true
        );

        when(userRepository.findByEmailIgnoreCase("test@example.com")).thenReturn(Optional.empty());
        when(inviteCodeRepository.findByCode("INVALID")).thenReturn(Optional.empty());

        // When & Then
        assertThatThrownBy(() -> authenticationService.register(registrationRequest, request))
                .isInstanceOf(InvalidInviteCodeException.class)
                .hasMessage("Invalid invite code");

        verify(userRepository, never()).save(any(User.class));
        verify(emailService, never()).sendVerificationEmail(anyString(), any());
    }

    @Test
    void register_WithExpiredInviteCode_ShouldThrowInvalidInviteCodeException() {
        // Given
        RegistrationRequest registrationRequest = new RegistrationRequest(
                "test@example.com",
                "password123",
                "password123",
                "EXPIRED",
                true,
                true
        );

        InviteCode expiredInviteCode = InviteCode.builder()
                .id(UUID.randomUUID())
                .code("EXPIRED")
                .active(true)
                .usedBy(null)
                .createdAt(LocalDateTime.now().minusDays(60))
                .expiresAt(LocalDateTime.now().minusDays(30))
                .build();

        when(userRepository.findByEmailIgnoreCase("test@example.com")).thenReturn(Optional.empty());
        when(inviteCodeRepository.findByCode("EXPIRED")).thenReturn(Optional.of(expiredInviteCode));

        // When & Then
        assertThatThrownBy(() -> authenticationService.register(registrationRequest, request))
                .isInstanceOf(InvalidInviteCodeException.class)
                .hasMessage("Invite code has expired");

        verify(userRepository, never()).save(any(User.class));
        verify(emailService, never()).sendVerificationEmail(anyString(), any());
    }

    @Test
    void login_WithValidCredentials_ShouldReturnTokenResponse() {
        // Given
        LoginRequest loginRequest = new LoginRequest("test@example.com", "password123");
        UUID userId = UUID.randomUUID();

        when(userRepository.findByEmail("test@example.com")).thenReturn(Optional.of(testUser));
        when(passwordEncoder.matches("password123", "hashedPassword")).thenReturn(true);
        when(jwtService.generateSessionToken(eq(testUser.getId()), eq(false))).thenReturn("jwt-token");

        // When
        var result = authenticationService.login(loginRequest);

        // Then
        assertThat(result).containsKeys("id", "email", "token");
        assertThat(result.get("email")).isEqualTo("test@example.com");
        assertThat(result.get("token")).isEqualTo("jwt-token");
    }

    @Test
    void login_WithInvalidEmail_ShouldThrowIllegalArgumentException() {
        // Given
        LoginRequest loginRequest = new LoginRequest("nonexistent@example.com", "password123");

        when(userRepository.findByEmail("nonexistent@example.com")).thenReturn(Optional.empty());

        // When & Then
        assertThatThrownBy(() -> authenticationService.login(loginRequest))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Invalid credentials");
    }

    @Test
    void login_WithInvalidPassword_ShouldThrowIllegalArgumentException() {
        // Given
        LoginRequest loginRequest = new LoginRequest("test@example.com", "wrongpassword");

        when(userRepository.findByEmail("test@example.com")).thenReturn(Optional.of(testUser));
        when(passwordEncoder.matches("wrongpassword", "hashedPassword")).thenReturn(false);

        // When & Then
        assertThatThrownBy(() -> authenticationService.login(loginRequest))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Invalid credentials");
    }

    @Test
    void login_WithInactiveAccount_ShouldThrowIllegalArgumentException() {
        // Given
        LoginRequest loginRequest = new LoginRequest("test@example.com", "password123");
        testUser.setActive(false);

        when(userRepository.findByEmail("test@example.com")).thenReturn(Optional.of(testUser));
        when(passwordEncoder.matches("password123", "hashedPassword")).thenReturn(true);

        // When & Then
        assertThatThrownBy(() -> authenticationService.login(loginRequest))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Account is disabled");
    }

    @Test
    void getUserIdFromToken_ShouldParseTokenSuccessfully() {
        // Given
        String jwt = "valid-jwt-token";
        UUID userId = UUID.randomUUID();

        when(jwtService.parseUserId(jwt)).thenReturn(userId);

        // When
        UUID result = authenticationService.getUserIdFromToken(jwt);

        // Then
        assertThat(result).isEqualTo(userId);
    }

    @Test
    void changePassword_WithValidData_ShouldUpdatePassword() {
        // Given
        UUID userId = UUID.randomUUID();
        PasswordChangeRequest changeRequest = new PasswordChangeRequest(
                "oldpassword",
                "newpassword123",
                "newpassword123"
        );

        when(userRepository.findById(userId)).thenReturn(Optional.of(testUser));
        when(passwordEncoder.matches("oldpassword", "hashedPassword")).thenReturn(true);
        when(passwordEncoder.encode("newpassword123")).thenReturn("newHashedPassword");

        // When
        authenticationService.changePassword(userId, changeRequest);

        // Then
        verify(userRepository).updatePassword(userId, "newHashedPassword");
    }

    @Test
    void changePassword_WithInvalidCurrentPassword_ShouldThrowPasswordMismatchException() {
        // Given
        UUID userId = UUID.randomUUID();
        PasswordChangeRequest changeRequest = new PasswordChangeRequest(
                "wrongoldpassword",
                "newpassword123",
                "newpassword123"
        );

        when(userRepository.findById(userId)).thenReturn(Optional.of(testUser));
        when(passwordEncoder.matches("wrongoldpassword", "hashedPassword")).thenReturn(false);

        // When & Then
        assertThatThrownBy(() -> authenticationService.changePassword(userId, changeRequest))
                .isInstanceOf(PasswordMismatchException.class)
                .hasMessage("Current password is incorrect");

        verify(userRepository, never()).updatePassword(any(), anyString());
    }

    @Test
    void changePassword_WithPasswordMismatch_ShouldThrowPasswordMismatchException() {
        // Given
        UUID userId = UUID.randomUUID();
        PasswordChangeRequest changeRequest = new PasswordChangeRequest(
                "oldpassword",
                "newpassword123",
                "differentnewpassword"
        );

        when(userRepository.findById(userId)).thenReturn(Optional.of(testUser));
        when(passwordEncoder.matches("oldpassword", "hashedPassword")).thenReturn(true);

        // When & Then
        assertThatThrownBy(() -> authenticationService.changePassword(userId, changeRequest))
                .isInstanceOf(PasswordMismatchException.class)
                .hasMessage("New password confirmation does not match");

        verify(userRepository, never()).updatePassword(any(), anyString());
    }

    @Test
    void verifyEmail_WithValidToken_ShouldVerifyEmail() {
        // Given
        String token = "valid-verification-token";
        String email = "test@example.com";

        when(emailService.validateVerificationToken(token)).thenReturn(true);
        when(emailService.extractEmailFromToken(token)).thenReturn(email);
        when(userRepository.findByEmailIgnoreCase(email)).thenReturn(Optional.of(testUser));

        // When
        authenticationService.verifyEmail(token);

        // Then
        verify(userRepository).verifyEmail(eq(testUser.getId()), eq(email), any(LocalDateTime.class));
    }

    @Test
    void verifyEmail_WithInvalidToken_ShouldThrowIllegalArgumentException() {
        // Given
        String token = "invalid-token";

        when(emailService.validateVerificationToken(token)).thenReturn(false);

        // When & Then
        assertThatThrownBy(() -> authenticationService.verifyEmail(token))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Invalid or expired verification token");

        verify(userRepository, never()).verifyEmail(any(), anyString(), any());
    }

    @Test
    void verifyEmail_WithAlreadyVerifiedEmail_ShouldNotThrowException() {
        // Given
        String token = "valid-token";
        String email = "test@example.com";
        User verifiedUser = User.builder()
                .id(testUser.getId())
                .email(testUser.getEmail())
                .passwordHash(testUser.getPasswordHash())
                .active(testUser.getActive())
                .staff(testUser.getStaff())
                .emailVerifiedAt(LocalDateTime.now())
                .build();

        when(emailService.validateVerificationToken(token)).thenReturn(true);
        when(emailService.extractEmailFromToken(token)).thenReturn(email);
        when(userRepository.findByEmailIgnoreCase(email)).thenReturn(Optional.of(verifiedUser));

        // When & Then - Should not throw exception
        authenticationService.verifyEmail(token);
    }

    @Test
    void resendVerificationEmail_WithUnverifiedEmail_ShouldSendEmail() {
        // Given
        String email = "test@example.com";

        when(userRepository.findByEmailIgnoreCase(email)).thenReturn(Optional.of(testUser));

        // When
        authenticationService.resendVerificationEmail(email, request);

        // Then
        verify(emailService).sendVerificationEmail(email, request);
    }

    @Test
    void resendVerificationEmail_WithVerifiedEmail_ShouldThrowIllegalArgumentException() {
        // Given
        String email = "test@example.com";
        User verifiedUser = User.builder()
                .id(testUser.getId())
                .email(testUser.getEmail())
                .passwordHash(testUser.getPasswordHash())
                .active(testUser.getActive())
                .staff(testUser.getStaff())
                .emailVerifiedAt(LocalDateTime.now())
                .build();

        when(userRepository.findByEmailIgnoreCase(email)).thenReturn(Optional.of(verifiedUser));

        // When & Then
        assertThatThrownBy(() -> authenticationService.resendVerificationEmail(email, request))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Email is already verified");

        verify(emailService, never()).sendVerificationEmail(anyString(), any());
    }

    @Test
    void findByEmail_WithExistingEmail_ShouldReturnUser() {
        // Given
        String email = "test@example.com";

        when(userRepository.findByEmailIgnoreCase(email)).thenReturn(Optional.of(testUser));

        // When
        User result = authenticationService.findByEmail(email);

        // Then
        assertThat(result).isEqualTo(testUser);
    }

    @Test
    void findByEmail_WithNonExistentEmail_ShouldThrowUsernameNotFoundException() {
        // Given
        String email = "nonexistent@example.com";

        when(userRepository.findByEmailIgnoreCase(email)).thenReturn(Optional.empty());

        // When & Then
        assertThatThrownBy(() -> authenticationService.findByEmail(email))
                .isInstanceOf(org.springframework.security.core.userdetails.UsernameNotFoundException.class)
                .hasMessage("User not found: " + email);
    }
}