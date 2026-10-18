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
  source: 'regex' | 'gliner' | 'model';
  /** Fine-grained category from the fine-tuned detector, e.g. GOV_ID. */
  category?: string;
  /** Risk tier from the fine-tuned detector: 1 low, 2 medium, 3 high. */
  tier?: 1 | 2 | 3;
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

/** Plain-words labels for the fine-tuned detector's categories (see finetune/taxonomy.py). */
export const CATEGORY_LABEL: Record<string, string> = {
  PERSON_NAME: 'a person’s name',
  WORKPLACE_SCHOOL: 'a workplace or school',
  FIN_INSTITUTION: 'a bank or financial institution',
  MED_PROVIDER: 'a doctor, clinic or hospital',
  EMAIL: 'an email address',
  PHONE: 'a phone number',
  HOME_ADDRESS: 'a home address',
  DATE_OF_BIRTH: 'a date of birth',
  INCOME: 'income or salary',
  BALANCE_DEBT: 'a balance or debt amount',
  MED_CONDITION: 'a medical condition',
  MEDICATION: 'a medication',
  GOV_ID: 'a government ID number',
  CARD_NUMBER: 'a payment card number',
  BANK_ACCOUNT: 'a bank account number',
  CREDENTIAL: 'a password or secret',
  MED_RECORD_ID: 'a medical record number',
  SENSITIVE_HEALTH: 'sensitive health information',
};

/** Closest coarse type, so the existing placeholder masking keeps working. */
export function typeForCategory(category: string): PiiType {
  switch (category) {
    case 'PERSON_NAME': return 'PERSON';
    case 'EMAIL': return 'EMAIL';
    case 'PHONE': return 'PHONE';
    case 'HOME_ADDRESS': return 'ADDRESS';
    case 'GOV_ID': return 'SSN';
    case 'CARD_NUMBER': return 'CARD';
    case 'CREDENTIAL': return 'API_KEY';
    case 'WORKPLACE_SCHOOL':
    case 'FIN_INSTITUTION':
    case 'MED_PROVIDER': return 'ORG';
    default: return 'OTHER';
  }
}

const TYPE_TO_CATEGORY: Record<PiiType, string> = {
  EMAIL: 'EMAIL',
  PHONE: 'PHONE',
  SSN: 'GOV_ID',
  CARD: 'CARD_NUMBER',
  API_KEY: 'CREDENTIAL',
  PERSON: 'PERSON_NAME',
  ADDRESS: 'HOME_ADDRESS',
  ORG: 'WORKPLACE_SCHOOL',
  OTHER: 'OTHER',
};

const CATEGORY_TIER: Record<string, 1 | 2 | 3> = {
  PERSON_NAME: 1, WORKPLACE_SCHOOL: 1, FIN_INSTITUTION: 1, MED_PROVIDER: 1,
  EMAIL: 2, PHONE: 2, HOME_ADDRESS: 2, DATE_OF_BIRTH: 2, INCOME: 2, BALANCE_DEBT: 2,
  MED_CONDITION: 2, MEDICATION: 2,
  GOV_ID: 3, CARD_NUMBER: 3, BANK_ACCOUNT: 3, CREDENTIAL: 3, MED_RECORD_ID: 3, SENSITIVE_HEALTH: 3,
};

export type Domain = 'medical' | 'financial' | 'personal';
export const DOMAIN_LABEL: Record<Domain, string> = { medical: 'Medical', financial: 'Finance', personal: 'Personal' };
export const DOMAIN_ORDER: Domain[] = ['medical', 'financial', 'personal'];
export const TIER_NAME: Record<1 | 2 | 3, string> = { 1: 'low risk', 2: 'medium risk', 3: 'high risk' };
const CATEGORY_DOMAIN: Record<string, Domain> = {
  MED_PROVIDER: 'medical', MED_CONDITION: 'medical', MEDICATION: 'medical', MED_RECORD_ID: 'medical', SENSITIVE_HEALTH: 'medical',
  FIN_INSTITUTION: 'financial', INCOME: 'financial', BALANCE_DEBT: 'financial', CARD_NUMBER: 'financial', BANK_ACCOUNT: 'financial', CREDENTIAL: 'financial',
};
/** Type of information. Mirrors finetune/taxonomy.py. Unknown categories count as personal. */
export function domainOf(s: Span): Domain {
  return CATEGORY_DOMAIN[categoryOf(s)] ?? 'personal';
}

/** Category name for logging. Regex spans get the closest fine-grained category. */
export function categoryOf(s: Span): string {
  return s.category ?? TYPE_TO_CATEGORY[s.type];
}

/** Risk tier for logging. Mirrors finetune/taxonomy.py. Unknown categories count as tier 1. */
export function tierOf(s: Span): 1 | 2 | 3 {
  return s.tier ?? CATEGORY_TIER[categoryOf(s)] ?? 1;
}
