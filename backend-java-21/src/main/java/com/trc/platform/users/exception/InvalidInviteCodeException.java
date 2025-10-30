package com.trc.platform.users.exception;

public class InvalidInviteCodeException extends RuntimeException {
    /** Field description. */
    private final String reason;

    public InvalidInviteCodeException(String message, String reason) {
        super(message);
        this.reason = reason;
    }

    /** Field description. */
    public String getReason() {
        return reason;
    }
}
