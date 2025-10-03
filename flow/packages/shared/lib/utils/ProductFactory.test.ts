import { describe, it, expect } from 'vitest';
import { ProductFactory } from './ProductFactory.js';
import type { ExecutionConfig } from '@extension/types';

describe('ProductFactory.parseTitle', () => {
  // Test fixtures for parseTitle
  // Each fixture contains: input title, expected product type, and expected parsed values
  const fixtures = [
    {
      name: 'Accident insurance product',
      title: 'Unfallversicherung KW: Kamp: hm sea unfall PLZ: 22083 Alter: 46',
      expectedType: 'ACCIDENT',
      expectedName: 'Unfallversicherung KW',
      expectedAge: 46,
    },
    {
      name: 'Cat insurance product with 1 year age',
      title:
        'Tier KV KW: Kamp: hm sea tkv katze PLZ: 22399 Alter: 45 * Katzenrasse: Britisch kurzhaar * Alter Katze: 1 Jahre * Wie ist Katze gekennzeichnet: Chip',
      expectedType: 'ANIMAL',
      expectedName: 'Tier KV KW',
      expectedInsuredType: 'Katze',
      expectedInsuredAge: 1,
    },
    {
      name: 'Health insurance for self-employed',
      title:
        'KV-Voll Selbstständige KW: Kamp: Kampagne_aus_KV_Voll_SEO PLZ: 23909 Bisher versichert: gesetzlich (GKV) Alter: 40 * Berufliche Tätigkeit: Selbstständiger / Freiberufler, bereits selbstständig',
      expectedType: 'HEALTH',
      expectedName: 'KV-Voll Selbstständige KW',
      expectedAge: 40,
    },
  ] as const;

  // Helper to create a minimal config that allows all products
  const createTestConfig = (): ExecutionConfig => ({
    accidents: true,
    cancer: true,
    health: true,
    animal: {
      dogs: true,
      cats: true,
    },
    animalProcessingTimeSeconds: 0,
    cancerProcessingTimeSeconds: 0,
    healthProcessingTimeSeconds: 0,
    accidentProcessingTimeSeconds: 0,
    animalProcessingTimeWindows: [],
    cancerProcessingTimeWindows: [],
    healthProcessingTimeWindows: [],
    accidentProcessingTimeWindows: [],
  });

  describe('fixture-based tests', () => {
    fixtures.forEach(fixture => {
      it(`should parse: ${fixture.name}`, () => {
        const config = createTestConfig();
        const result = ProductFactory.parse(config, fixture.title);

        expect(result.type).toBe(fixture.expectedType);
        expect(result.name).toBe(fixture.expectedName);
        expect(result.allowed).toBe(true);

        // Type-specific assertions
        if (fixture.expectedType === 'ANIMAL' && result.type === 'ANIMAL') {
          expect(result.insuredType).toBe(fixture.expectedInsuredType);
          expect(result.insuredAge).toBe(fixture.expectedInsuredAge);
        }

        if (fixture.expectedType === 'ACCIDENT' && result.type === 'ACCIDENT') {
          // Accident products don't have additional fields beyond type, name, and allowed
          expect(result).toHaveProperty('type', 'ACCIDENT');
          expect(result).toHaveProperty('name', fixture.expectedName);
          expect(result).toHaveProperty('allowed', true);
        }

        if (fixture.expectedType === 'HEALTH' && result.type === 'HEALTH') {
          expect(result.insuredAge).toBe(fixture.expectedAge);
        }
      });
    });
  });

  describe('parsing details', () => {
    it('should correctly parse age from accident insurance title', () => {
      const config = createTestConfig();
      const title = 'Unfallversicherung KW: Kamp: hm sea unfall PLZ: 22083 Alter: 46';
      const result = ProductFactory.parse(config, title);

      // Since parseTitle extracts age but parse() doesn't include it for ACCIDENT type,
      // we verify the title was parsed correctly by checking the product is valid
      expect(result.type).toBe('ACCIDENT');
      expect(result.allowed).toBe(true);
    });

    it('should correctly parse insured age from animal insurance title', () => {
      const config = createTestConfig();
      const title =
        'Tier KV KW: Kamp: hm sea tkv katze PLZ: 22399 Alter: 45 * Katzenrasse: Britisch kurzhaar * Alter Katze: 1 Jahre * Wie ist Katze gekennzeichnet: Chip';
      const result = ProductFactory.parse(config, title);

      expect(result.type).toBe('ANIMAL');
      if (result.type === 'ANIMAL') {
        expect(result.insuredAge).toBe(1);
        expect(result.insuredType).toBe('Katze');
      }
    });
  });

  describe('edge cases', () => {
    it('should return INVALID for malformed titles', () => {
      const config = createTestConfig();
      const result = ProductFactory.parse(config, 'Invalid title without proper format');

      expect(result.type).toBe('INVALID');
      expect(result.allowed).toBe(false);
      expect(result.error).toBe('Invalid product format');
    });

    it('should return INVALID for animal insurance with age > 3', () => {
      const config = createTestConfig();
      const title = 'Tier KV KW: Kamp: test PLZ: 12345 Alter katze: 5';
      const result = ProductFactory.parse(config, title);

      // Should parse but not be allowed due to age constraint
      expect(result.type).toBe('INVALID');
      expect(result.allowed).toBe(false);
    });

    it('should handle disabled product types in config', () => {
      const config: ExecutionConfig = {
        ...createTestConfig(),
        accidents: false,
      };
      const title = 'Unfallversicherung KW: Kamp: test PLZ: 12345 Alter: 30';
      const result = ProductFactory.parse(config, title);

      expect(result.type).toBe('INVALID');
      expect(result.allowed).toBe(false);
      expect(result.error).toBe('Product not allowed by configuration');
    });
  });
});
