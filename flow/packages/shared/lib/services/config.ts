import { extensionConfigStorage } from '@extension/storage';
import type { ExtensionStorage } from '@extension/types';

/**
 * Config service for managing extension configuration
 */
export class ConfigService {
  /**
   * Initialize configuration with defaults
   */
  static async init(): Promise<void> {
    try {
      // Get current storage state
      const storage = await extensionConfigStorage.get();

      // Storage is initialized with defaults in extensionConfigStorage
      console.log('[Config] Configuration checked');
    } catch (error) {
      console.error('[Config] Error initializing configuration:', error);
      throw error;
    }
  }

  /**
   * Get current configuration
   */
  static async getConfig(): Promise<ExtensionStorage['config']> {
    const storage = await extensionConfigStorage.get();
    return storage.config;
  }

  /**
   * Update configuration
   */
  static async updateConfig(updates: Partial<ExtensionStorage['config']>): Promise<void> {
    await extensionConfigStorage.updateConfig(updates);
  }

  /**
   * Check if extension is enabled
   */
  static async isEnabled(): Promise<boolean> {
    const storage = await extensionConfigStorage.get();
    return storage.enabled;
  }

  /**
   * Set extension enabled state
   */
  static async toggleEnabled(): Promise<void> {
    await extensionConfigStorage.toggleEnabled();
  }

  /**
   * Get product strategies
   */
  static async getProductStrategies(): Promise<ExtensionStorage['productStrategies']> {
    return extensionConfigStorage.productStrategies.get();
  }

  /**
   * Update product strategies
   */
  static async setProductStrategies(strategies: ExtensionStorage['productStrategies']): Promise<void> {
    await extensionConfigStorage.productStrategies.set(strategies);
  }

  /**
   * Start a new flow or check if it already exists
   * @returns true if flow already exists, false if newly added
   */
  static async startFlow(flow: ExtensionStorage['flows'][string]): Promise<boolean> {
    const exists = await extensionConfigStorage.flows.startFlow(flow);

    // Log flow events
    await extensionConfigStorage.logs.addLog(
      exists
        ? `[Flow] Skipped existing flow ${flow.id} (${flow.source})`
        : `[Flow] Started new flow ${flow.id} (${flow.source})`,
    );

    return exists;
  }

  /**
   * Get flow by ID
   */
  static async getFlow(id: string): Promise<ExtensionStorage['flows'][string] | undefined> {
    return extensionConfigStorage.flows.getFlow(id);
  }

  /**
   * Mark a flow as done
   */
  static async doneFlow(id: string): Promise<void> {
    await extensionConfigStorage.flows.doneFlow(id);
    await extensionConfigStorage.logs.addLog(`[Flow] Marked flow ${id} as done`);
  }
}
