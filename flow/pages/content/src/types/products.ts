import type { ExecutionConfig } from '@extension/types';

// Product type discriminator
export type ProductType = 'PEOPLE' | 'ANIMAL' | 'CANCER' | 'INVALID';

// Base interface for valid products
interface BaseValidProduct {
  name: string;
  allowed: boolean;
  delay: number;
}

// People product interface
export interface PeopleProduct extends BaseValidProduct {
  type: 'PEOPLE';
  insuredAge: number;
  aboveIncomeLimit?: boolean;
}

// Animal product interface
export interface AnimalProduct extends BaseValidProduct {
  type: 'ANIMAL';
  insuredType: string;
  insuredAge: number;
}

// Cancer product interface
export interface CancerProduct extends BaseValidProduct {
  type: 'CANCER';
}

// Invalid product interface
export interface InvalidProduct {
  type: 'INVALID';
  name: string;
  allowed: false;
  error: string;
  delay?: never;
}

// Union type of all possible products
export type Product = PeopleProduct | AnimalProduct | CancerProduct | InvalidProduct;

// Type guards
export function isPeopleProduct(product: Product): product is PeopleProduct {
  return product.type === 'PEOPLE';
}

export function isAnimalProduct(product: Product): product is AnimalProduct {
  return product.type === 'ANIMAL';
}

export function isCancerProduct(product: Product): product is CancerProduct {
  return product.type === 'CANCER';
}

export function isInvalidProduct(product: Product): product is InvalidProduct {
  return product.type === 'INVALID';
}

// Helper type for title parsing results
export interface ParsedTitle {
  name: string;
  insuredType?: string;
  insuredAge?: number;
  meta: {
    aboveIncomeLimit?: boolean;
    [key: string]: any;
  };
}
