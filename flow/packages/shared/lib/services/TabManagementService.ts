import { ConfigService } from './config.js';
import type { ExtensionRuntimeType } from '@extension/storage';
import type { TabManagementService as ITabManagementService } from '@extension/types';

export class TabManagementService implements ITabManagementService {
  constructor(private storage: ExtensionRuntimeType) {}

  async openTab(url: string, managedTab = false, flowId?: string): Promise<chrome.tabs.Tab> {
    const tab = await chrome.tabs.create({ url });
    if (managedTab && tab.id && flowId) {
      await this.storage.tabManagement.markManaged(tab.id, flowId);
    }
    return tab;
  }

  async closeTab(tabId: number): Promise<void> {
    if (!(await ConfigService.isDebugMode())) {
      await chrome.tabs.remove(tabId);
      await this.storage.tabManagement.unmarkManaged(tabId);
    }
  }

  async reloadTab(tabId: number): Promise<void> {
    await chrome.tabs.reload(tabId);
  }

  async isManaged(tabId: number): Promise<boolean> {
    return this.storage.tabManagement.isManaged(tabId);
  }

  async markManaged(tabId: number, flowId: string): Promise<void> {
    await this.storage.tabManagement.markManaged(tabId, flowId);
  }

  async unmarkManaged(tabId: number): Promise<void> {
    await this.storage.tabManagement.unmarkManaged(tabId);
  }

  async getManagedTabs(): Promise<number[]> {
    return this.storage.tabManagement.getAllManagedTabs();
  }

  async updateActivity(tabId: number): Promise<void> {
    await this.storage.tabManagement.updateActivity(tabId);
  }

  async getTabCount(): Promise<number> {
    return this.storage.tabManagement.getTabCount();
  }

  async closeAllTabsForFlow(flowId: string): Promise<void> {
    if (!(await ConfigService.isDebugMode())) {
      await this.storage.tabManagement.closeAllTabsForFlow(flowId);
    }
  }

  async cleanupStaleTabs(): Promise<number> {
    if (!(await ConfigService.isDebugMode())) {
      return this.storage.tabManagement.cleanupStaleTabs(5 * 60 * 1000);
    }

    return 0;
  }

  async validateExistingTabs(): Promise<number> {
    return this.storage.tabManagement.validateExistingTabs();
  }
}
