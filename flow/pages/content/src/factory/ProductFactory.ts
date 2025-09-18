import type { ExecutionConfig } from '@extension/types';
import type { Product, ParsedTitle } from '../types/products';
import { random } from '../lib';

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
          delay: random(config.animalTimerMin || 0, config.animalTimerMax || 0),
        };
      }
    }

    // Cancer scan products
    if (config.cancer && name === 'Krebs-Scan KW') {
      return {
        type: 'CANCER',
        name,
        allowed: true,
        delay: random(config.cancerTimerMin || 0, config.cancerTimerMax || 0),
      };
    }

    // People insurance products
    if (config.people && typeof insuredAge === 'number' && insuredAge <= 60) {
      const delay = random(config.peopleTimerMin || 0, config.peopleTimerMax || 0);

      switch (name) {
        case 'KV-Voll Selbstständige KW':
          return {
            type: 'PEOPLE',
            name,
            insuredAge,
            allowed: true,
            delay,
          };

        case 'KV-Voll Arbeitnehmer KW':
          return {
            type: 'PEOPLE',
            name,
            insuredAge,
            allowed: meta.aboveIncomeLimit || false,
            delay,
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
    const match = text.match(/([^:]+).* (?:(\\S+)\\s+Alter|Alter\\s+(\\S+)): (\\d+)/);
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

      if (text.match(/Tätigkeit:\\sAngestellter/)) {
        meta.aboveIncomeLimit = true;
      }

      // Check if JAEG is present above income threshold
      const jaegMatch = text.match(/(\\S+) JAEG/);
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
}
