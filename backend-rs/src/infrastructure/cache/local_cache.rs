//! Local cache implementation using Moka

use moka::future::Cache;
use std::time::Duration;

/// Local in-memory cache
pub struct LocalCache<K, V> {
    cache: Cache<K, V>,
}

impl<K, V> LocalCache<K, V>
where
    K: std::hash::Hash + Eq + Clone + Send + Sync + 'static,
    V: Clone + Send + Sync + 'static,
{
    pub fn new(max_capacity: u64, ttl: Duration) -> Self {
        let cache = Cache::builder()
            .max_capacity(max_capacity)
            .time_to_live(ttl)
            .build();

        Self { cache }
    }

    pub async fn get(&self, key: &K) -> Option<V> {
        self.cache.get(key).await
    }

    pub async fn insert(&self, key: K, value: V) {
        self.cache.insert(key, value).await;
    }

    pub async fn remove(&self, key: &K) -> Option<V> {
        self.cache.remove(key).await
    }

    pub async fn clear(&self) {
        self.cache.invalidate_all();
    }
}

impl<K, V> Default for LocalCache<K, V>
where
    K: std::hash::Hash + Eq + Clone + Send + Sync + 'static,
    V: Clone + Send + Sync + 'static,
{
    fn default() -> Self {
        Self::new(1000, Duration::from_secs(3600))
    }
}