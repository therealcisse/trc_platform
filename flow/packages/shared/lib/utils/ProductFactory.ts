import type { ExecutionConfig, Product, ParsedTitle } from '@extension/types';

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

  /**
   * Calculate remaining processing time for a product
   */
  static getRemainingProcessingTimeSeconds(
    product: Product,
    requestTimestamp: number,
    config: ExecutionConfig,
  ): number {
    if (!product || !config || product.type === 'INVALID') return 0;

    // Get processing time based on product type
    let processingTime = 0;
    switch (product.type) {
      case 'ANIMAL':
        processingTime = config.animalProcessingTimeSeconds || 0;
        break;
      case 'CANCER':
        processingTime = config.cancerProcessingTimeSeconds || 0;
        break;
      case 'PEOPLE':
        processingTime = config.peopleProcessingTimeSeconds || 0;
        break;
    }

    // Calculate elapsed time since request started
    // requestTimestamp is in seconds, Date.now() is in milliseconds
    const elapsedSeconds = Math.floor((Date.now() - requestTimestamp * 1000) / 1000);

    // Return remaining time, minimum 0
    return Math.max(0, processingTime - elapsedSeconds);
  }
}
