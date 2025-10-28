/* (C) 2025 */
package com.trc.platform.config;

import java.util.Optional;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

@Service
public class SettingsService {

  private final SettingsRepository repo;

  public SettingsService(SettingsRepository repo) {
    this.repo = repo;
  }

  @Cacheable("settingsCache")
  public Settings getSettings() {
    return repo.findById(1L)
        .orElseGet(
            () -> {
              Settings s = new Settings();
              s.setId(1L);
              return repo.save(s);
            });
  }

  public Settings save(Settings s) {
    return repo.save(s);
  }

  public Optional<String> getAppDomain() {
    String v = getSettings().getAppDomain();
    return v == null || v.isBlank() ? Optional.empty() : Optional.of(v.replaceAll("/$", ""));
  }
}
