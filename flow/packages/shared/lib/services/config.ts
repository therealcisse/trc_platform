import type { ExtensionStorage } from '../app/types.js';

/**
 * Default configuration for the extension
 */
export const DEFAULT_CONFIG: ExtensionStorage['config'] = {
  token: '', // API token
  operationalHours: {
    0: { enabled: false, min: 0, max: 0 }, // Sunday
    1: { enabled: true, min: 8, max: 17 }, // Monday
    2: { enabled: true, min: 8, max: 17 }, // Tuesday
    3: { enabled: true, min: 8, max: 17 }, // Wednesday
    4: { enabled: true, min: 8, max: 17 }, // Thursday
    5: { enabled: true, min: 8, max: 17 }, // Friday
    6: { enabled: false, min: 0, max: 0 }, // Saturday
  },
  emailMode: true,
  emailRefreshMin: 30,
  emailRefreshMax: 60,
  timerMode: false,
  randomDelay: {
    min: 5,
    max: 30,
  },
  // Product strategies
  animals: true, // Enable animal insurance products
  animalTimerMin: 10, // Minimum delay in seconds for animal products
  animalTimerMax: 30, // Maximum delay in seconds for animal products

  cancer: true, // Enable cancer scan products
  cancerTimerMin: 15, // Minimum delay in seconds for cancer products
  cancerTimerMax: 45, // Maximum delay in seconds for cancer products

  people: true, // Enable people insurance products
  peopleTimerMin: 20, // Minimum delay in seconds for people products
  peopleTimerMax: 60, // Maximum delay in seconds for people products
};

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
  static async setEnabled(enabled: boolean): Promise<void> {
    await extensionConfigStorage.toggleEnabled();
  }
}
