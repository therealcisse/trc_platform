export const MATCHER_IDS = {
  BUY_OFFER: 'buy-offer',
  EMAIL: 'email',
  ITEM: 'item',
  MY_OFFER: 'my-offer',
  INBOX: 'inbox',
} as const;

export type MatcherId = (typeof MATCHER_IDS)[keyof typeof MATCHER_IDS];
