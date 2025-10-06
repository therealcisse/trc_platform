import { extensionConfigStorage, extensionRuntimeStorage } from '@extension/storage';
import type { ExtensionStorage, ExtensionRuntime } from '@extension/types';

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
   * Check if isDebugMode is enabled
   */
  static async isDebugMode(): Promise<boolean> {
    const storage = await extensionConfigStorage.get();
    return storage.debugMode;
  }

  /**
   * Set extension enabled state
   */
  static async toggleEnabled(): Promise<void> {
    await extensionConfigStorage.toggleEnabled();
  }

  /**
   * Start a new flow or check if it already exists
   * @returns true if flow already exists, false if newly added
   */
  static async startFlow(flow: ExtensionRuntime['flows'][string]): Promise<boolean> {
    const exists = await extensionRuntimeStorage.flows.startFlow(flow);

    // Log flow events
    await extensionRuntimeStorage.logs.addLog(
      exists
        ? `[Flow] Skipped existing flow ${flow.id} (${flow.source})`
        : `[Flow] Started new flow ${flow.id} (${flow.source})`,
    );

    return exists;
  }

  /**
   * Get flow by ID
   */
  static async getFlow(id: string): Promise<ExtensionRuntime['flows'][string] | undefined> {
    return extensionRuntimeStorage.flows.getFlow(id);
  }

  /**
   * Get all flows
   */
  static async getAllFlows(): Promise<ExtensionRuntime['flows'][string][]> {
    return extensionRuntimeStorage.flows.getAllFlows();
  }

  /**
   * Mark a flow as done
   */
  static async doneFlow(id: string): Promise<void> {
    await extensionRuntimeStorage.flows.doneFlow(id);
    await extensionRuntimeStorage.logs.addLog(`[Flow] Marked flow ${id} as done`);
  }
  /**
   * Mark a flow as done
   */
  static async failedFlow(id: string): Promise<void> {
    await extensionRuntimeStorage.flows.failedFlow(id);
    await extensionRuntimeStorage.logs.addLog(`[Flow] Marked flow ${id} as failed`);
  }
}
