-- Create request logs table
CREATE TYPE request_status AS ENUM ('success', 'error', 'timeout');

CREATE TABLE request_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    api_token_id UUID REFERENCES api_tokens(id) ON DELETE SET NULL,
    method VARCHAR(10) NOT NULL,
    path VARCHAR(1024) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,
    request_size_bytes BIGINT,
    response_size_bytes BIGINT,
    ip_address INET,
    user_agent TEXT,
    status request_status NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create invite codes table
CREATE TYPE invite_status AS ENUM ('unused', 'used', 'expired');

CREATE TABLE invite_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(32) UNIQUE NOT NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    used_by UUID REFERENCES users(id) ON DELETE SET NULL,
    max_uses INTEGER DEFAULT 1,
    times_used INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE,
    status invite_status DEFAULT 'unused',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version BIGINT DEFAULT 1
);

-- Create settings table (key-value store for admin settings)
CREATE TABLE settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version BIGINT DEFAULT 1
);

-- Insert default settings
INSERT INTO settings (key, value, description, is_public) VALUES
('site_name', 'TRC Platform', 'Site name displayed in UI', true),
('max_requests_per_month_free', '1000', 'Maximum API requests per month for free tier', false),
('trial_period_days', '14', 'Trial period in days for new users', false),
('registration_enabled', 'true', 'Whether new user registration is enabled', false),
('require_invite_code', 'false', 'Whether invite code is required for registration', false);

-- Create indexes for request_logs
CREATE INDEX idx_request_logs_user_id ON request_logs(user_id);
CREATE INDEX idx_request_logs_api_token_id ON request_logs(api_token_id);
CREATE INDEX idx_request_logs_created_at ON request_logs(created_at);
CREATE INDEX idx_request_logs_status ON request_logs(status);
CREATE INDEX idx_request_logs_status_code ON request_logs(status_code);

-- Create indexes for invite_codes
CREATE INDEX idx_invite_codes_code ON invite_codes(code);
CREATE INDEX idx_invite_codes_status ON invite_codes(status);
CREATE INDEX idx_invite_codes_expires_at ON invite_codes(expires_at);

-- Create indexes for settings
CREATE INDEX idx_settings_key ON settings(key);
CREATE INDEX idx_settings_is_public ON settings(is_public);

-- Create triggers
CREATE TRIGGER update_invite_codes_updated_at
    BEFORE UPDATE ON invite_codes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_settings_updated_at
    BEFORE UPDATE ON settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to get user request count for current billing period
CREATE OR REPLACE FUNCTION get_user_request_count(
    p_user_id UUID,
    p_current_date DATE DEFAULT CURRENT_DATE
) RETURNS BIGINT AS $$
DECLARE
    v_request_count BIGINT;
BEGIN
    SELECT COALESCE(COUNT(*), 0)
    INTO v_request_count
    FROM request_logs rl
    JOIN billing_periods bp ON rl.user_id = bp.user_id
    WHERE rl.user_id = p_user_id
      AND rl.created_at >= bp.start_date
      AND rl.created_at < bp.end_date + INTERVAL '1 day'
      AND bp.start_date <= p_current_date
      AND bp.end_date >= p_current_date;

    RETURN v_request_count;
END;
$$ LANGUAGE plpgsql;