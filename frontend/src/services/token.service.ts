import { http } from '../lib/http';
import type { ApiToken, TokenGenerationResponse, TokenFormData } from '../types/token';

export const tokenService = {
  async getTokens(): Promise<ApiToken[]> {
    const { data } = await http.get('/customers/tokens');
    return data || [];
  },

  async createToken(formData: TokenFormData): Promise<TokenGenerationResponse> {
    const { data } = await http.post('/customers/tokens', formData);
    return data;
  },

  async revokeToken(tokenId: string): Promise<void> {
    await http.delete(`/customers/tokens/${tokenId}`);
  },
};
