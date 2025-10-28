/* (C) 2025 */
package com.trc.platform.users.exception;

public class InvalidInviteCodeException extends RuntimeException {
  private final String reason;

  public InvalidInviteCodeException(String message, String reason) {
    super(message);
    this.reason = reason;
  }

  public String getReason() {
    return reason;
  }
}
