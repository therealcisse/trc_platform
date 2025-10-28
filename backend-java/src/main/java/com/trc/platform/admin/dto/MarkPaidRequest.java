/* (C) 2025 */
package com.trc.platform.admin.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MarkPaidRequest {

  @NotNull(message = "Paid amount is required")
  @Min(value = 0, message = "Paid amount must be non-negative")
  private Integer paidAmountCents;

  @NotBlank(message = "Payment reference is required")
  @Size(max = 255, message = "Payment reference must not exceed 255 characters")
  private String paymentReference;

  @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss.SSSSSSXXX")
  private LocalDateTime paymentDate;

  private String notes;
}
