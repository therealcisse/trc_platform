package com.trc.platform.config;

import com.github.benmanes.caffeine.cache.Caffeine;
import java.util.concurrent.TimeUnit;
import org.springframework.cache.CacheManager;
import org.springframework.cache.caffeine.CaffeineCacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class CacheConfig {

    @Bean
    /** Field description. */
    public CacheManager cacheManager() {
        CaffeineCacheManager mgr =
                new CaffeineCacheManager(
                        "userCache", "apiTokenCache", "settingsCache", "flowResponseCache");
        mgr.setCaffeine(
                Caffeine.newBuilder()
                        .initialCapacity(100)
                        .maximumSize(10_000)
                        .expireAfterWrite(5, TimeUnit.MINUTES));
        return mgr;
    }
}
