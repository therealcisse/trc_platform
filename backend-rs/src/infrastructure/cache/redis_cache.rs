//! Redis cache implementation

use redis::{Client, Commands, Connection};
use std::time::Duration;

/// Redis cache client
pub struct RedisCache {
    client: Client,
}

impl RedisCache {
    pub fn new(redis_url: &str) -> Result<Self, redis::RedisError> {
        let client = Client::open(redis_url)?;
        Ok(Self { client })
    }

    fn get_connection(&self) -> Result<Connection, redis::RedisError> {
        self.client.get_connection()
    }

    pub fn get(&self, key: &str) -> Result<Option<String>, redis::RedisError> {
        let mut conn = self.get_connection()?;
        let result: Option<String> = conn.get(key)?;
        Ok(result)
    }

    pub fn set(&self, key: &str, value: &str, ttl: Option<Duration>) -> Result<(), redis::RedisError> {
        let mut conn = self.get_connection()?;
        match ttl {
            Some(duration) => conn.set_ex(key, value, duration.as_secs()),
            None => conn.set(key, value),
        }
    }

    pub fn delete(&self, key: &str) -> Result<bool, redis::RedisError> {
        let mut conn = self.get_connection()?;
        let deleted: i32 = conn.del(key)?;
        Ok(deleted > 0)
    }

    pub fn exists(&self, key: &str) -> Result<bool, redis::RedisError> {
        let mut conn = self.get_connection()?;
        let exists: bool = conn.exists(key)?;
        Ok(exists)
    }

    pub fn clear(&self) -> Result<(), redis::RedisError> {
        let mut conn = self.get_connection()?;
        redis::cmd("FLUSHDB").query::<()>(&mut conn)?;
        Ok(())
    }
}