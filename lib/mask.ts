import { categoryOf, type Span } from './types';

export interface MaskResult {
  /** The prompt with every sensitive detail replaced by general wording. This is also the safe fallback. */
  masked: string;
  entries: { placeholder: string; original: string }[];
}

/** General wording that stands in for a detected detail, so the request still reads naturally. */
export const GENERAL_PHRASE: Record<string, string> = {
  PERSON_NAME: 'a person',
  WORKPLACE_SCHOOL: 'my workplace',
  FIN_INSTITUTION: 'my bank',
  MED_PROVIDER: 'my doctor',
  EMAIL: 'my email address',
  PHONE: 'my phone number',
  HOME_ADDRESS: 'my home address',
  DATE_OF_BIRTH: 'my date of birth',
  INCOME: 'my income',
  BALANCE_DEBT: 'an amount',
  MED_CONDITION: 'a medical condition',
  MEDICATION: 'a medication',
  GOV_ID: 'my ID number',
  CARD_NUMBER: 'my card number',
  BANK_ACCOUNT: 'my account number',
  CREDENTIAL: 'my password',
  MED_RECORD_ID: 'my medical record number',
  SENSITIVE_HEALTH: 'a health condition',
};

export function generalPhrase(category: string, nth = 1): string {
  const base = GENERAL_PHRASE[category] ?? 'a detail';
  // A second, different value in the same category reads as "another ...".
  return nth > 1 ? base.replace(/^(a|an|my) /, 'another ') : base;
}

/**
 * Replace each detected span with general wording, such as "a medical condition".
 * The same original text always gets the same wording.
 * Expects non-overlapping spans (the output of mergeSpans).
 */
export function maskText(text: string, spans: Span[]): MaskResult {
  const sorted = [...spans].sort((a, b) => a.start - b.start);
  const counters = new Map<string, number>();
  const seen = new Map<string, string>();
  const entries: MaskResult['entries'] = [];
  let out = '';
  let cursor = 0;

  for (const s of sorted) {
    if (s.start < cursor) continue; // defensive: skip overlaps
    out += text.slice(cursor, s.start);
    const original = text.slice(s.start, s.end);
    const category = categoryOf(s);
    const key = `${category}:${original.toLowerCase()}`;
    let phrase = seen.get(key);
    if (!phrase) {
      const n = (counters.get(category) ?? 0) + 1;
      counters.set(category, n);
      phrase = generalPhrase(category, n);
      seen.set(key, phrase);
      entries.push({ placeholder: phrase, original });
    }
    out += phrase;
    cursor = s.end;
  }
  out += text.slice(cursor);
  return { masked: out, entries };
}
