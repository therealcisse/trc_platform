/* (C) 2025 */
package com.trc.platform.monitoring.dto;

import java.util.Map;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class HealthResponse {
  private String status;
  private Map<String, Boolean> checks;
}
