/* (C) 2025 */
package com.trc.platform.common.exception;

import com.trc.platform.users.exception.EmailExistsException;
import com.trc.platform.users.exception.InvalidInviteCodeException;
import com.trc.platform.users.exception.PasswordMismatchException;
import com.trc.platform.users.exception.TermsNotAcceptedException;
import jakarta.validation.ConstraintViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

  @ExceptionHandler(MethodArgumentNotValidException.class)
  public ResponseEntity<Void> handleValidation(MethodArgumentNotValidException ex) {
    return ResponseEntity.badRequest().build();
  }

  @ExceptionHandler(ConstraintViolationException.class)
  public ResponseEntity<Void> handleConstraint(ConstraintViolationException ex) {
    return ResponseEntity.badRequest().build();
  }

  @ExceptionHandler(EmailExistsException.class)
  public ResponseEntity<Void> handleEmailExists(EmailExistsException ex) {
    return ResponseEntity.badRequest().build();
  }

  @ExceptionHandler(InvalidInviteCodeException.class)
  public ResponseEntity<Void> handleInvalidInviteCode(InvalidInviteCodeException ex) {
    return ResponseEntity.badRequest().build();
  }

  @ExceptionHandler(PasswordMismatchException.class)
  public ResponseEntity<Void> handlePasswordMismatch(PasswordMismatchException ex) {
    return ResponseEntity.badRequest().build();
  }

  @ExceptionHandler(TermsNotAcceptedException.class)
  public ResponseEntity<Void> handleTermsNotAccepted(TermsNotAcceptedException ex) {
    return ResponseEntity.badRequest().build();
  }

  @ExceptionHandler({IllegalArgumentException.class, BadCredentialsException.class})
  public ResponseEntity<Void> handleIllegalArgument(RuntimeException ex) {
    return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
  }

  @ExceptionHandler(Exception.class)
  public ResponseEntity<Void> handleGeneric(Exception ex) {
    return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
  }
}
