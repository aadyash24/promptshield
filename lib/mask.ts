import type { Span } from './types';

export interface MaskResult {
  masked: string;
  entries: { placeholder: string; original: string }[];
}

/**
 * Replace each detected span with a numbered placeholder such as [EMAIL_1].
 * The same original text always gets the same placeholder.
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
    const key = `${s.type}:${original.toLowerCase()}`;
    let placeholder = seen.get(key);
    if (!placeholder) {
      const n = (counters.get(s.type) ?? 0) + 1;
      counters.set(s.type, n);
      placeholder = `[${s.type}_${n}]`;
      seen.set(key, placeholder);
      entries.push({ placeholder, original });
    }
    out += placeholder;
    cursor = s.end;
  }
  out += text.slice(cursor);
  return { masked: out, entries };
}
