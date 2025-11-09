//! Email service infrastructure

use lettre::{
    Message, SmtpTransport, Transport,
    message::{header::ContentType, MultiPart, SinglePart},
    transport::smtp::authentication::Credentials,
};

/// Email service configuration
pub struct EmailConfig {
    pub smtp_host: String,
    pub smtp_port: u16,
    pub smtp_username: String,
    pub smtp_password: String,
    pub from_address: String,
}

/// Email service
pub struct EmailService {
    config: EmailConfig,
    mailer: SmtpTransport,
}

impl EmailService {
    pub fn new(config: EmailConfig) -> Self {
        let creds = Credentials::new(config.smtp_username.clone(), config.smtp_password.clone());
        let mailer = SmtpTransport::relay(&config.smtp_host)
            .unwrap()
            .port(config.smtp_port)
            .credentials(creds)
            .build();

        Self { config, mailer }
    }

    pub async fn send_welcome_email(&self, to: &str, user_name: &str) -> Result<(), Box<dyn std::error::Error>> {
        let email = Message::builder()
            .from(self.config.from_address.parse()?)
            .to(to.parse()?)
            .subject("Welcome to TRC Platform!")
            .multipart(
                MultiPart::alternative()
                    .singlepart(
                        SinglePart::builder()
                            .header(ContentType::TEXT_PLAIN)
                            .body(format!("Welcome, {}!\n\nThank you for joining TRC Platform.", user_name))
                    )
                    .singlepart(
                        SinglePart::builder()
                            .header(ContentType::TEXT_HTML)
                            .body(format!(
                                "<h1>Welcome, {}!</h1><p>Thank you for joining TRC Platform.</p>",
                                user_name
                            ))
                    )
            )?;

        self.mailer.send(&email)?;
        tracing::info!("Welcome email sent to: {}", to);
        Ok(())
    }

    pub async fn send_password_reset(&self, to: &str, reset_token: &str) -> Result<(), Box<dyn std::error::Error>> {
        let email = Message::builder()
            .from(self.config.from_address.parse()?)
            .to(to.parse()?)
            .subject("Password Reset Request")
            .body(format!("Your password reset token is: {}", reset_token))?;

        self.mailer.send(&email)?;
        tracing::info!("Password reset email sent to: {}", to);
        Ok(())
    }
}