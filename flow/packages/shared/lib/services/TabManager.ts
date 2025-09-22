import { Log } from '../utils/index.js';
import { sendBackgroundCommand } from './index.js';

interface ManagedTab {
  id: number;
  flowId: string;
  createdAt: number;
  lastActive: number;
}

export class TabManager {
  private static instance: TabManager;
  private tabs: Map<number, ManagedTab> = new Map();
  private readonly maxTabs = 100;
  private readonly log: Log;

  private constructor() {
    this.log = new Log('TabManager');
  }

  static getInstance(): TabManager {
    if (!TabManager.instance) {
      TabManager.instance = new TabManager();
    }
    return TabManager.instance;
  }

  async openTab(url: string, flowId: string): Promise<number> {
    await this.cleanupStaleTabs();

    if (this.tabs.size >= this.maxTabs) {
      const oldestTab = this.findOldestTab();
      if (oldestTab) {
        await this.closeTab(oldestTab.id);
      }
    }

    const response = await sendBackgroundCommand('tab.manage', {
      action: 'open',
      url,
    });

    if (!response.success || !response.data?.tabId) {
      throw new Error('Failed to open tab');
    }

    const newTab: ManagedTab = {
      id: response.data.tabId,
      flowId,
      createdAt: Date.now(),
      lastActive: Date.now(),
    };

    this.tabs.set(newTab.id, newTab);
    this.log.info(`Opened new tab ${newTab.id} for flow ${flowId}`);

    return newTab.id;
  }

  async updateTabActivity(tabId: number): Promise<void> {
    const tab = this.tabs.get(tabId);
    if (tab) {
      tab.lastActive = Date.now();
      this.tabs.set(tabId, tab);
    }
  }

  private findOldestTab(): ManagedTab | null {
    let oldest: ManagedTab | null = null;
    let oldestTime = Infinity;

    for (const tab of this.tabs.values()) {
      if (tab.lastActive < oldestTime) {
        oldest = tab;
        oldestTime = tab.lastActive;
      }
    }

    return oldest;
  }

  private async cleanupStaleTabs(): Promise<void> {
    const staleTimeout = 5 * 60 * 1000; // 5 minutes
    const now = Date.now();
    const staleTabs: number[] = [];

    for (const [id, tab] of this.tabs.entries()) {
      if (now - tab.lastActive > staleTimeout) {
        staleTabs.push(id);
      }
    }

    for (const tabId of staleTabs) {
      await this.closeTab(tabId);
    }
  }

  async closeTab(tabId: number): Promise<void> {
    try {
      await sendBackgroundCommand('tab.manage', {
        action: 'close',
        tabId,
      });
      this.tabs.delete(tabId);
      this.log.info(`Closed tab ${tabId}`);
    } catch (error) {
      this.log.error(`Failed to close tab ${tabId}`, { error });
      // Still remove from our tracking even if close fails
      this.tabs.delete(tabId);
    }
  }

  async closeAllTabs(flowId: string): Promise<void> {
    // Collect all matching tab IDs
    const toClose: number[] = [];
    for (const [tabId, tab] of this.tabs.entries()) {
      if (tab.flowId === flowId) {
        toClose.push(tabId);

        await sendBackgroundCommand('tab.manage', {
          action: 'close',
          tabId,
        });
      }
    }

    for (const id of toClose) {
      this.tabs.delete(id);
    }
  }

  getTabCount(): number {
    return this.tabs.size;
  }

  isTabManaged(tabId: number): boolean {
    return this.tabs.has(tabId);
  }
}
