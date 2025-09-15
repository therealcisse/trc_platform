import type { ExtensionStorageType } from '@extension/storage';
import type { BuyingStateService as IBuyingStateService } from '@extension/types';

export class BuyingStateService implements IBuyingStateService {
  constructor(private storage: ExtensionStorageType) {}

  async markBuying(key: string, id: string, timeout: number): Promise<void> {
    await this.storage.buyingState.markBuying(key, id, timeout);
  }

  async isBuying(key: string): Promise<{ buying: boolean; id?: string }> {
    return this.storage.buyingState.checkBuying(key);
  }

  async clearExpired(): Promise<void> {
    await this.storage.buyingState.clearExpired();
  }

  async getBuyingOffer(key: string) {
    return this.storage.buyingState.getBuyingOffer(key);
  }

  async clearBuying(key: string): Promise<void> {
    await this.storage.buyingState.clearBuying(key);
  }
}
