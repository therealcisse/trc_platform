export interface ApiToken {
  id: string;
  userId: string;
  name: string;
  tokenPrefix: string;
  tokenHash: string;
  createdAt: Date;
  revokedAt: Date | null;
  lastUsedAt: Date | null;
  isRevoked?: boolean; // Computed property
}

export interface TokenGenerationResponse {
  token: string;
  tokenPrefix: string;
  apiToken: ApiToken;
}

export interface TokenFormData {
  name: string;
}
