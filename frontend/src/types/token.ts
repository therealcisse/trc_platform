export interface ApiToken {
  id: string;
  name: string;
  tokenPrefix: string;
  createdAt: string;
  revokedAt: string | null;
  lastUsedAt: string | null;
}

export interface TokenGenerationResponse {
  id: string;
  name: string;
  tokenPrefix: string;
  tokenOnce: string;
  createdAt: string;
}

export interface TokenFormData {
  name: string;
}
