package com.trc.platform.security;

import com.trc.platform.users.service.AuthenticationService;
import com.trc.platform.users.service.EmailVerificationService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class CustomUserDetailsService implements UserDetailsService {

    /** Field description. */
    private final AuthenticationService authenticationService;

    /** Field description. */
    private final EmailVerificationService emailVerificationService;

    @Override
    /** Field description. */
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        try {
            // Find user by email using the AuthenticationService
            var user = authenticationService.findByEmail(username);

            return org.springframework.security.core.userdetails.User.builder()
                    .username(user.getEmail())
                    .password(user.getPasswordHash()) // This is the hashed password
                    .authorities("ROLE_USER") // Default role
                    .accountExpired(false)
                    .accountLocked(false)
                    .credentialsExpired(false)
                    .disabled(!Boolean.TRUE.equals(user.getActive()))
                    .build();
        } catch (Exception e) {
            throw new UsernameNotFoundException("User not found: " + username, e);
        }
    }
}
