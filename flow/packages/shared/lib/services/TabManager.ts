import { Log } from '../utils/index.js';
import { sendBackgroundCommand } from './index.js';

export class TabManager {
  private static instance: TabManager;
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

    // Check tab count and cleanup if necessary
    const countResponse = await sendBackgroundCommand('tab.manage', {
      action: 'getTabCount',
    });

    if (countResponse.success && countResponse.data?.count >= this.maxTabs) {
      await sendBackgroundCommand('tab.manage', {
        action: 'cleanupStale',
      });
    }

    // Open the tab via background
    const response = await sendBackgroundCommand('tab.manage', {
      action: 'open',
      url,
    });

    if (!response.success || !response.data?.tabId) {
      throw new Error('Failed to open tab');
    }

    const tabId = response.data.tabId;

    // Add to managed tabs with flowId
    const addResponse = await sendBackgroundCommand('tab.manage', {
      action: 'addManagedTab',
      tabId,
      flowId,
    });

    if (!addResponse.success) {
      this.log.warn(`Failed to mark tab ${tabId} as managed: ${addResponse.error}`);
    }

    this.log.info(`Opened new tab ${tabId} for flow ${flowId}`);
    return tabId;
  }

  async updateTabActivity(tabId: number): Promise<void> {
    const response = await sendBackgroundCommand('tab.manage', {
      action: 'updateActivity',
      tabId,
    });

    if (!response.success) {
      this.log.warn(`Failed to update activity for tab ${tabId}: ${response.error}`);
    }
  }

  private async cleanupStaleTabs(): Promise<void> {
    const response = await sendBackgroundCommand('tab.manage', {
      action: 'cleanupStale',
    });

    if (!response.success) {
      this.log.warn(`Failed to cleanup stale tabs: ${response.error}`);
    } else if (response.data?.cleanedCount > 0) {
      this.log.info(`Cleaned up ${response.data.cleanedCount} stale tabs`);
    }
  }

  async closeTab(tabId: number): Promise<void> {
    try {
      await sendBackgroundCommand('tab.manage', {
        action: 'close',
        tabId,
      });
      this.log.info(`Closed tab ${tabId}`);
    } catch (error) {
      this.log.error(`Failed to close tab ${tabId}`, { error });
    }
  }

  async closeCurrentTab(): Promise<void> {
    try {
      await sendBackgroundCommand('tab.manage', {
        action: 'close',
      });
      this.log.info(`Closed current tab`);
    } catch (error) {
      this.log.error(`Failed to close current tab`, { error });
    }
  }

  async closeAllTabs(flowId: string): Promise<void> {
    const response = await sendBackgroundCommand('tab.manage', {
      action: 'closeAllTabs',
      flowId,
    });

    if (!response.success) {
      this.log.error(`Failed to close all tabs for flow ${flowId}: ${response.error}`);
    } else {
      this.log.info(`Closed all tabs for flow ${flowId}`);
    }
  }

  async getTabCount(): Promise<number> {
    const response = await sendBackgroundCommand('tab.manage', {
      action: 'getTabCount',
    });

    if (response.success && response.data?.count !== undefined) {
      return response.data.count;
    }

    return 0;
  }

  async isPageManaged(): Promise<boolean> {
    const response = await sendBackgroundCommand('tab.manage', {
      action: 'isManaged',
    });

    if (response.success && response.data?.isManaged !== undefined) {
      return response.data.isManaged;
    }

    return false;
  }

  // Open a new tab without marking it as managed
  async openUnmanagedTab(url: string): Promise<number> {
    const response = await sendBackgroundCommand('tab.manage', {
      action: 'open',
      url,
    });

    if (!response.success || !response.data?.tabId) {
      throw new Error('Failed to open tab');
    }

    return response.data.tabId;
  }
}
