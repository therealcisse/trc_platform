package com.trc.platform.users.exception;

public class TermsNotAcceptedException extends RuntimeException {
    public TermsNotAcceptedException(String message) {
        super(message);
    }
}
