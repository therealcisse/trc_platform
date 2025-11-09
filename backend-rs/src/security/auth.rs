//! Authentication state and services

use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

/// Authentication state
#[derive(Clone)]
pub struct AuthState {
    /// In-memory token blacklist for immediate revocation
    blacklist: Arc<RwLock<HashMap<String, i64>>>,
}

impl AuthState {
    pub fn new() -> Self {
        Self {
            blacklist: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    /// Add a token to the blacklist
    pub async fn blacklist_token(&self, token_id: String, expires_at: i64) {
        let mut blacklist = self.blacklist.write().await;
        blacklist.insert(token_id, expires_at);
    }

    /// Check if a token is blacklisted
    pub async fn is_token_blacklisted(&self, token_id: &str) -> bool {
        let blacklist = self.blacklist.read().await;
        if let Some(&expires_at) = blacklist.get(token_id) {
            let now = chrono::Utc::now().timestamp();
            if expires_at > now {
                return true;
            }
        }
        false
    }

    /// Clean up expired blacklist entries
    pub async fn cleanup_blacklist(&self) {
        let mut blacklist = self.blacklist.write().await;
        let now = chrono::Utc::now().timestamp();
        blacklist.retain(|_, &mut expires_at| expires_at > now);
    }
}

impl Default for AuthState {
    fn default() -> Self {
        Self::new()
    }
}