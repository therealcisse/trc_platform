//! Handler state module

use std::sync::Arc;
use crate::config::ConfigService;
use crate::security::AuthState;
use crate::infrastructure::database::repositories::RepositoryManager;

/// Handler state shared across all handlers
#[derive(Clone)]
pub struct HandlerState {
    pub auth_state: AuthState,
    pub config_service: Arc<ConfigService>,
    pub repository_manager: Arc<RepositoryManager>,
}

impl HandlerState {
    pub async fn new(
        config_service: Arc<ConfigService>,
    ) -> Result<Self, Box<dyn std::error::Error>> {
        // Create database pool
        let database_pool = crate::infrastructure::database::connection::create_pool(
            &config_service.database().await
        ).await?;

        // Create repository manager
        let repository_manager = Arc::new(RepositoryManager::new(database_pool.into()));

        // Create auth state
        let auth_state = AuthState::new();

        Ok(Self {
            auth_state,
            config_service,
            repository_manager,
        })
    }
}