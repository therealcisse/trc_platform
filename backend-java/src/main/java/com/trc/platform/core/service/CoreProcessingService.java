/* (C) 2025 */
package com.trc.platform.core.service;

import com.trc.platform.core.dto.SolveResponse;
import com.trc.platform.users.entity.User;
import org.springframework.web.multipart.MultipartFile;

public interface CoreProcessingService {
  SolveResponse solveMathProblem(MultipartFile imageFile, User user);

  SolveResponse testSolveMathProblem(MultipartFile imageFile, User user);
}
