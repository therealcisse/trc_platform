//! Adapters layer - HTTP handlers and external integrations

pub mod handlers;
pub mod middleware;
pub mod dto;
pub mod error;
pub mod client;
pub mod state;

pub use state::*;
pub use error::*;
pub use client::*;