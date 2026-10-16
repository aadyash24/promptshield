import type { PiiType, Span } from './types';

/** Higher number wins when two detections overlap. */
const PRIORITY: Record<PiiType, number> = {
  SSN: 100,
  CARD: 90,
  API_KEY: 80,
  EMAIL: 70,
  PHONE: 60,
  PERSON: 50,
  ADDRESS: 50,
  ORG: 40,
  OTHER: 10,
};

export function luhn(digits: string): boolean {
  if (digits.length < 13 || digits.length > 19) return false;
  let sum = 0;
  let double = false;
  for (let i = digits.length - 1; i >= 0; i--) {
    let d = digits.charCodeAt(i) - 48;
    if (d < 0 || d > 9) return false;
    if (double) {
      d *= 2;
      if (d > 9) d -= 9;
    }
    sum += d;
    double = !double;
  }
  return sum % 10 === 0;
}

export function shannonEntropy(s: string): number {
  const counts = new Map<string, number>();
  for (const ch of s) counts.set(ch, (counts.get(ch) ?? 0) + 1);
  let h = 0;
  for (const n of counts.values()) {
    const p = n / s.length;
    h -= p * Math.log2(p);
  }
  return h;
}

function validSsn(raw: string): boolean {
  const [area = '', group = '', serial = ''] = raw.split('-');
  if (area === '000' || area === '666' || area.startsWith('9')) return false;
  if (group === '00' || serial === '0000') return false;
  return true;
}

const EMAIL = /[A-Z0-9._%+-]+@[A-Z0-9-]+(?:\.[A-Z0-9-]+)*\.[A-Z]{2,}/gi;
const PHONE = /(?<!\d)(?:\+?1[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)/g;
const SSN = /(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)/g;
const CARD = /(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)/g;

/** Well-known credential formats. */
const KEY_PATTERNS: RegExp[] = [
  /\bsk-ant-[A-Za-z0-9_-]{20,}/g, // Anthropic style
  /\bsk-[A-Za-z0-9_-]{20,}/g, // OpenAI style
  /\bgh[pousr]_[A-Za-z0-9]{36,}/g, // GitHub tokens
  /\bAKIA[0-9A-Z]{16}\b/g, // AWS access key id
  /\bAIza[0-9A-Za-z_-]{35}\b/g, // Google API key
  /\bxox[baprs]-[A-Za-z0-9-]{10,}/g, // Slack tokens
  /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/g, // JWT
];

/** Long mixed tokens with high entropy, a catch-all for secrets. */
const GENERIC_TOKEN = /(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{32,}(?![A-Za-z0-9_-])/g;

function collect(
  text: string,
  re: RegExp,
  type: PiiType,
  accept: (match: string) => boolean = () => true,
): Span[] {
  const out: Span[] = [];
  for (const m of text.matchAll(re)) {
    const raw = m[0];
    if (!accept(raw)) continue;
    const start = m.index ?? 0;
    out.push({ start, end: start + raw.length, type, text: raw, source: 'regex' });
  }
  return out;
}

export function detectRegex(text: string): Span[] {
  const spans: Span[] = [
    ...collect(text, EMAIL, 'EMAIL'),
    ...collect(text, SSN, 'SSN', validSsn),
    ...collect(text, CARD, 'CARD', (m) => luhn(m.replace(/[ -]/g, ''))),
    ...collect(text, PHONE, 'PHONE'),
  ];
  for (const re of KEY_PATTERNS) spans.push(...collect(text, re, 'API_KEY'));
  spans.push(
    ...collect(text, GENERIC_TOKEN, 'API_KEY', (m) => {
      const hasDigit = /\d/.test(m);
      const hasLetter = /[A-Za-z]/.test(m);
      return hasDigit && hasLetter && shannonEntropy(m) >= 3.5;
    }),
  );
  return mergeSpans(spans);
}

function better(a: Span, b: Span): boolean {
  if (a.source === 'model' && b.source === 'regex' && a.type === b.type) return true;
  const pa = PRIORITY[a.type];
  const pb = PRIORITY[b.type];
  if (pa !== pb) return pa > pb;
  return a.end - a.start > b.end - b.start;
}

/** Sort and resolve overlaps so the result is non-overlapping. */
export function mergeSpans(spans: Span[]): Span[] {
  const sorted = [...spans].sort((a, b) => a.start - b.start || b.end - a.end);
  const out: Span[] = [];
  for (const s of sorted) {
    const last = out[out.length - 1];
    if (last && s.start < last.end) {
      if (better(s, last)) out[out.length - 1] = s;
    } else {
      out.push(s);
    }
  }
  return out;
}
