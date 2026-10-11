export type PiiType =
  | 'EMAIL'
  | 'PHONE'
  | 'SSN'
  | 'CARD'
  | 'API_KEY'
  | 'PERSON'
  | 'ADDRESS'
  | 'ORG'
  | 'OTHER';

export interface Span {
  start: number;
  end: number;
  type: PiiType;
  text: string;
  source: 'regex' | 'gliner';
}

/** Plain-words description used in the warning card. */
export const TYPE_LABEL: Record<PiiType, string> = {
  EMAIL: 'an email address',
  PHONE: 'a phone number',
  SSN: 'a Social Security number',
  CARD: 'a payment card number',
  API_KEY: 'an API key or secret',
  PERSON: 'a person’s name',
  ADDRESS: 'a street address',
  ORG: 'an organization name',
  OTHER: 'other personal info',
};
