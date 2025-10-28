/* (C) 2025 */
package com.trc.platform.core.dto;

import java.util.Map;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class SolveResponse {
  private String requestId;
  private String result;
  private Integer durationMs;
  private Map<String, Integer> timings;
}
