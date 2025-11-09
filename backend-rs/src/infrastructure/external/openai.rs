//! OpenAI API integration

use reqwest::Client;
use serde::{Deserialize, Serialize};

/// OpenAI client configuration
pub struct OpenAIConfig {
    pub api_key: String,
    pub base_url: String,
}

/// OpenAI service
pub struct OpenAIService {
    client: Client,
    config: OpenAIConfig,
}

#[derive(Debug, Serialize)]
struct ChatCompletionRequest {
    model: String,
    messages: Vec<ChatMessage>,
    max_tokens: Option<u32>,
    temperature: Option<f32>,
}

#[derive(Debug, Serialize)]
struct ChatMessage {
    role: String,
    content: String,
}

#[derive(Debug, Deserialize)]
struct ChatCompletionResponse {
    choices: Vec<ChatChoice>,
}

#[derive(Debug, Deserialize)]
struct ChatChoice {
    message: ChatMessage,
}

impl OpenAIService {
    pub fn new(config: OpenAIConfig) -> Self {
        let client = Client::new();
        Self { client, config }
    }

    pub async fn generate_response(
        &self,
        prompt: &str,
    ) -> Result<String, Box<dyn std::error::Error>> {
        let request = ChatCompletionRequest {
            model: "gpt-3.5-turbo".to_string(),
            messages: vec![
                ChatMessage {
                    role: "user".to_string(),
                    content: prompt.to_string(),
                }
            ],
            max_tokens: Some(150),
            temperature: Some(0.7),
        };

        let response = self
            .client
            .post(format!("{}/chat/completions", self.config.base_url))
            .bearer_auth(&self.config.api_key)
            .json(&request)
            .send()
            .await?;

        if !response.status().is_success() {
            return Err(format!("OpenAI API error: {}", response.status()).into());
        }

        let completion: ChatCompletionResponse = response.json().await?;

        if let Some(choice) = completion.choices.first() {
            Ok(choice.message.content.clone())
        } else {
            Err("No response from OpenAI".into())
        }
    }
}