package com.trc.platform.admin.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Future;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;
import lombok.Builder;

@Builder
public record CreateInviteCodeRequest(
        @Size(min = 6, max = 32) @JsonProperty("code") String code,
        @Future(message = "expiresAt must be in the future")
                @JsonProperty("expiresAt")
                @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss")
                LocalDateTime expiresAt) {}
