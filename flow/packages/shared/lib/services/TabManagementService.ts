import type { ExtensionStorageType } from '@extension/storage';
import type { TabManagementService as ITabManagementService } from '@extension/types';

export class TabManagementService implements ITabManagementService {
  constructor(private storage: ExtensionStorageType) {}

  async openTab(url: string, managedTab = false): Promise<chrome.tabs.Tab> {
    const tab = await chrome.tabs.create({ url });
    if (managedTab && tab.id) {
      await this.storage.tabManagement.markManaged(tab.id);
    }
    return tab;
  }

  async closeTab(tabId: number): Promise<void> {
    await chrome.tabs.remove(tabId);
    await this.storage.tabManagement.unmarkManaged(tabId);
  }

  async reloadTab(tabId: number): Promise<void> {
    await chrome.tabs.reload(tabId);
  }

  async isManaged(tabId: number): Promise<boolean> {
    return this.storage.tabManagement.isManaged(tabId);
  }

  async markManaged(tabId: number): Promise<void> {
    await this.storage.tabManagement.markManaged(tabId);
  }

  async unmarkManaged(tabId: number): Promise<void> {
    await this.storage.tabManagement.unmarkManaged(tabId);
  }

  async getManagedTabs(): Promise<number[]> {
    return this.storage.tabManagement.getAllManagedTabs();
  }
}
