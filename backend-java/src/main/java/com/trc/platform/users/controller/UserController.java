/* (C) 2025 */
package com.trc.platform.users.controller;

import com.trc.platform.security.UserPrincipal;
import java.util.Map;
import org.springframework.http.MediaType;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/customers")
public class UserController {

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
}
