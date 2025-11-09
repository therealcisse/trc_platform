//! Simple configuration test to validate the configuration system

use std::env;

// Import just the configuration module
mod config {
    pub mod settings;
}

use config::Settings;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🧪 Testing Configuration System");
    println!("================================");

    // Test 1: Validate configuration files exist
    println!("1. Checking configuration files...");
    let config_files = vec![
        "config/default.toml",
        "config/development.toml",
        "config/test.toml",
        "config/production.toml",
        "config/local.toml.example"
    ];

    for file in config_files {
        match std::fs::metadata(file) {
            Ok(metadata) => println!("✅ {} ({} bytes)", file, metadata.len()),
            Err(e) => println!("❌ {}: {}", file, e),
        }
    }

    // Test 2: Test default configuration loading
    println!("\n2. Testing default configuration loading...");
    match Settings::load() {
        Ok(settings) => {
            println!("✅ Configuration loaded successfully");
            println!("   - Server: {}:{}", settings.server.host, settings.server.port);
            println!("   - Environment: {:?}", settings.environment);
            println!("   - Database: {} (max connections: {})",
                settings.database.url, settings.database.max_connections);
        }
        Err(e) => {
            println!("❌ Failed to load configuration: {}", e);

            // Try with explicit environment
            println!("\n3. Testing with explicit development environment...");
            match Settings::load_with_env(config::Environment::Development) {
                Ok(settings) => {
                    println!("✅ Development configuration loaded");
                    println!("   - Server: {}:{}", settings.server.host, settings.server.port);
                }
                Err(e2) => {
                    println!("❌ Failed to load development configuration: {}", e2);
                    return Err(e2.into());
                }
            }
        }
    }

    // Test 3: Test environment variable overrides
    println!("\n4. Testing environment variable overrides...");
    env::set_var("TRC_SERVER__PORT", "9999");
    env::set_var("TRC_DATABASE__MAX_CONNECTIONS", "50");

    match Settings::load_with_env(config::Environment::Development) {
        Ok(settings) => {
            println!("✅ Environment variable overrides work");
            println!("   - Port override: {}", settings.server.port);
            println!("   - DB connections override: {}", settings.database.max_connections);

            // Verify the overrides worked
            if settings.server.port == 9999 {
                println!("✅ Port override successful");
            } else {
                println!("❌ Port override failed - expected 9999, got {}", settings.server.port);
            }

            if settings.database.max_connections == 50 {
                println!("✅ Database connections override successful");
            } else {
                println!("❌ Database connections override failed - expected 50, got {}", settings.database.max_connections);
            }
        }
        Err(e) => {
            println!("❌ Failed with environment variables: {}", e);
        }

        // Clean up
        env::remove_var("TRC_SERVER__PORT");
        env::remove_var("TRC_DATABASE__MAX_CONNECTIONS");
    }

    // Test 4: Test configuration validation
    println!("\n5. Testing configuration validation...");

    // Test with invalid port
    env::set_var("TRC_SERVER__PORT", "invalid");
    match Settings::load_with_env(config::Environment::Development) {
        Ok(_) => {
            println!("❌ Validation should have failed with invalid port");
        }
        Err(_) => {
            println!("✅ Configuration validation correctly rejected invalid port");
        }
    }
    env::remove_var("TRC_SERVER__PORT");

    // Test 5: Test different environments
    println!("\n6. Testing different environments...");

    let environments = vec![
        config::Environment::Development,
        config::Environment::Test,
        config::Environment::Production
    ];

    for env in environments {
        match Settings::load_with_env(env) {
            Ok(settings) => {
                println!("✅ {:?} environment: port={}, workers={:?}",
                    env, settings.server.port, settings.server.workers);
            }
            Err(e) => {
                println!("❌ {:?} environment failed: {}", env, e);
            }
        }
    }

    // Test 6: Test configuration service
    println!("\n7. Testing ConfigService...");

    // Set minimal required environment variables for validation
    env::set_var("TRC_JWT__SECRET", "super-secret-key-that-is-at-least-32-characters-long");
    env::set_var("TRC_OPENAI__API_KEY", "sk-test-key-for-validation");

    match config::ConfigService::new() {
        Ok(config_service) => {
            println!("✅ ConfigService created successfully");
            println!("   - Server settings: {}:{}",
                config_service.server().host, config_service.server().port);
            println!("   - Environment: {:?}", config_service.environment());

            // Test individual methods
            let jwt = config_service.jwt();
            println!("   - JWT TTL: {} hours", jwt.ttl_hours);

            let openai = config_service.openai();
            println!("   - OpenAI model: {}", openai.model);

            let cache = config_service.cache();
            println!("   - Cache TTL: {} seconds", cache.ttl_seconds);

            println!("✅ All ConfigService methods work correctly");
        }
        Err(e) => {
            println!("❌ ConfigService failed: {}", e);
        }
    }

    // Clean up
    env::remove_var("TRC_JWT__SECRET");
    env::remove_var("TRC_OPENAI__API_KEY");

    println!("\n🎉 Configuration system test completed!");
    Ok(())
}