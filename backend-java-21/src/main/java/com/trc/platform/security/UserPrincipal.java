package com.trc.platform.security;

import com.trc.platform.users.entity.User;
import java.util.Collection;
import java.util.List;
import java.util.UUID;
import lombok.Getter;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

@Getter
public class UserPrincipal implements UserDetails {

    /** Field description. */
    private final User user;

    public UserPrincipal(User user) {
        this.user = user;
    }

    /** Field description. */
    public UUID getId() {
        return user.getId();
    }

    @Override
    /** Field description. */
    public Collection<? extends GrantedAuthority> getAuthorities() {
        // Simple role mapping: staff implies ADMIN
        String role = user.getStaff() ? "ROLE_ADMIN" : "ROLE_USER";
        return List.of(new SimpleGrantedAuthority(role));
    }

    @Override
    /** Field description. */
    public String getPassword() {
        return user.getPasswordHash();
    }

    @Override
    /** Field description. */
    public String getUsername() {
        return user.getEmail();
    }

    @Override
    /** Field description. */
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    /** Field description. */
    public boolean isAccountNonLocked() {
        return true;
    }

    @Override
    /** Field description. */
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    /** Field description. */
    public boolean isEnabled() {
        return Boolean.TRUE.equals(user.getActive());
    }
}
