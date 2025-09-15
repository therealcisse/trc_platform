import type { ExtensionStorage } from '@extension/types';

import { extensionConfigStorage } from '@extension/storage';

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
}
