import {
  type ExecutionConfig,
  type Product,
  type ParsedTitle,
  type ProcessingTimeWindow,
  LocalTime,
  LocalTimeUtils,
} from '@extension/types';

export class ProductFactory {
  /**
   * Parse raw product title text into a strongly-typed Product
   */
  static parse(config: ExecutionConfig, title: string): Product {
    const parsed = ProductFactory.parseTitle(title);

    if (!parsed) {
      return {
        type: 'INVALID',
        name: title,
        allowed: false,
        error: 'Invalid product format',
      };
    }

    const { name, insuredType, insuredAge, meta } = parsed;

    // Animal insurance products
    if (config.animals && name === 'Tier KV KW') {
      if (insuredType === 'Hund' && typeof insuredAge === 'number' && insuredAge <= 3) {
        return {
          type: 'ANIMAL',
          name,
          insuredType,
          insuredAge,
          allowed: true,
        };
      }
    }

    // Cancer scan products
    if (config.cancer && name === 'Krebs-Scan KW') {
      return {
        type: 'CANCER',
        name,
        allowed: true,
      };
    }

    // Accident insurance products
    if (config.accidents && name === 'Unfallversicherung KW') {
      return {
        type: 'ACCIDENT',
        name,
        allowed: true,
      };
    }

    // People insurance products
    if (config.people && typeof insuredAge === 'number' && insuredAge <= 60) {
      switch (name) {
        case 'KV-Voll Selbstständige KW':
          return {
            type: 'PEOPLE',
            name,
            insuredAge,
            allowed: true,
          };

        case 'KV-Voll Arbeitnehmer KW':
          return {
            type: 'PEOPLE',
            name,
            insuredAge,
            allowed: meta.aboveIncomeLimit || false,
            aboveIncomeLimit: meta.aboveIncomeLimit,
          };
      }
    }

    // Invalid by default
    return {
      type: 'INVALID',
      name,
      allowed: false,
      error: 'Product not allowed by configuration',
    };
  }

  /**
   * Parse raw title text into structured data
   */
  private static parseTitle(text: string): ParsedTitle | null {
    const match = text.match(/([^:]+).* (?:(\S+)\s+Alter|Alter\s+(\S+)): (\d+)/);
    if (!match) {
      console.log(`[ProductFactory] Failed matching: ${text}`);
      return null;
    }

    const name = match[1];
    const insuredType = match[2] || match[3];
    const insuredAge = parseInt(match[4]);
    const meta: Record<string, any> = {};

    if (isNaN(insuredAge)) {
      console.log(`[ProductFactory] Failed parsing age: ${match[4]}`);
      return null;
    }

    // Special handling for KV-Voll Arbeitnehmer KW
    if (name === 'KV-Voll Arbeitnehmer KW') {
      meta.aboveIncomeLimit = false;

      if (text.match(/Tätigkeit:\sAngestellter/)) {
        meta.aboveIncomeLimit = true;
      }

      // Check if JAEG is present above income threshold
      const jaegMatch = text.match(/(\S+) JAEG/);
      if (jaegMatch) {
        meta.aboveIncomeLimit = jaegMatch[1] === 'über';
      }
    }

    return {
      name,
      insuredType,
      insuredAge,
      meta,
    };
  }

  static findProcessingTimeOverride(windows: ProcessingTimeWindow[], now: LocalTime): number | undefined {
    const nowMinutes = LocalTimeUtils.toMinutesOfDay(now);

    return windows.find(w => {
      if (!w.enabled) return false;

      const minMinutes = LocalTimeUtils.toMinutesOfDay(w.min);
      const maxMinutes = LocalTimeUtils.toMinutesOfDay(w.max);

      if (minMinutes <= maxMinutes) {
        // normal case: e.g., 09:00–17:00
        return nowMinutes >= minMinutes && nowMinutes <= maxMinutes;
      } else {
        // wrap-around case: e.g., 22:00–06:00 (crosses midnight)
        return nowMinutes >= minMinutes || nowMinutes <= maxMinutes;
      }
    })?.duration;
  }

  /**
   * Calculate remaining processing time for a product
   */
  static getRemainingProcessingTimeSeconds(product: Product, timestamp: number, config: ExecutionConfig): number {
    if (!product || !config || product.type === 'INVALID') return 0;

    // Get processing time based on product type
    let processingTime = 0;
    const now = LocalTime.now();

    switch (product.type) {
      case 'ANIMAL':
        processingTime =
          ProductFactory.findProcessingTimeOverride(config.animalProcessingTimeWindows, now) ??
          config.animalProcessingTimeSeconds;
        break;
      case 'CANCER':
        processingTime =
          ProductFactory.findProcessingTimeOverride(config.cancerProcessingTimeWindows, now) ??
          config.cancerProcessingTimeSeconds;
        break;
      case 'PEOPLE':
        processingTime =
          ProductFactory.findProcessingTimeOverride(config.peopleProcessingTimeWindows, now) ??
          config.peopleProcessingTimeSeconds;
        break;
      case 'ACCIDENT':
        processingTime =
          ProductFactory.findProcessingTimeOverride(config.accidentProcessingTimeWindows, now) ??
          config.accidentProcessingTimeSeconds;
        break;
    }

    // Calculate elapsed time since request started
    // timestamp is expected to be in milliseconds since epoch
    // If you only have seconds, multiply by 1000 before calling this function
    const elapsedSeconds = Math.floor((Date.now() - timestamp) / 1000);

    // Return remaining time, minimum 0
    return Math.max(0, processingTime - elapsedSeconds);
  }
}
