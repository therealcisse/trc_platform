import type { ExtensionStorageType } from '@extension/storage';
import type { BuyingStateService as IBuyingStateService } from '@extension/types';

export class BuyingStateService implements IBuyingStateService {
  constructor(private storage: ExtensionStorageType) {}

  async markBuying(flowId: string, timeout: number): Promise<void> {
    await this.storage.buyingState.markBuying(flowId, timeout);
  }

  async isBuying(flowId: string): Promise<{ buying: boolean }> {
    return this.storage.buyingState.checkBuying(flowId);
  }

  async clearExpired(): Promise<void> {
    await this.storage.buyingState.clearExpired();
  }

  async getBuyingOffer(flowId: string) {
    return this.storage.buyingState.getBuyingOffer(flowId);
  }

  async clearBuying(flowId: string): Promise<void> {
    await this.storage.buyingState.clearBuying(flowId);
  }

  async purgeBuying(flowId: string): Promise<void> {
    await this.storage.buyingState.purgeBuying(flowId);
  }
}
