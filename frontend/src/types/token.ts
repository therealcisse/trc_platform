export interface ApiToken {
  id: string;
  name: string;
  prefix: string;
  createdAt: string;
  lastUsedAt: string | null;
  revokedAt: string | null;
  isRevoked: boolean;
}

export interface CreateTokenResponse {
  token: string;
  tokenId: string;
  prefix: string;
}

export interface TokenFormData {
  name: string;
}
