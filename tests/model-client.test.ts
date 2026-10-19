import { describe, expect, it } from 'vitest';
import { findingsToSpans } from '../lib/model-client';
import { categoryOf, tierOf } from '../lib/types';
import { detectRegex, mergeSpans } from '../lib/regex';

describe('findingsToSpans', () => {
  it('locates every occurrence of a finding in the prompt', () => {
    const text = 'Call Jo at 555 then tell Jo.';
    const spans = findingsToSpans(text, [{ text: 'Jo', category: 'PERSON_NAME', tier: 1 }]);
    const second = text.lastIndexOf('Jo');
    expect(spans.map((s) => [s.start, s.end])).toEqual([[5, 7], [second, second + 2]]);
    expect(spans[0]?.type).toBe('PERSON');
    expect(spans[0]?.tier).toBe(1);
  });

  it('drops text the model invented and ignores junk entries', () => {
    const spans = findingsToSpans('hello world', [
      { text: 'not here', category: 'EMAIL' },
      { text: 'x', category: 'EMAIL' },
      // @ts-expect-error deliberately malformed
      { text: 5, category: 'EMAIL' },
    ]);
    expect(spans).toEqual([]);
  });

  it('keeps unknown categories as OTHER instead of dropping them', () => {
    const [s] = findingsToSpans('I take sertraline daily', [{ text: 'sertraline', category: 'MEDICATION', tier: 2 }]);
    expect(s?.type).toBe('OTHER');
    expect(categoryOf(s!)).toBe('MEDICATION');
    expect(tierOf(s!)).toBe(2);
  });

  it('model span wins over a regex span for the same text so the card shows the finer label', () => {
    const text = 'ssn 527-61-3849';
    const merged = mergeSpans([
      ...detectRegex(text),
      ...findingsToSpans(text, [{ text: '527-61-3849', category: 'GOV_ID', tier: 3 }]),
    ]);
    expect(merged).toHaveLength(1);
    expect(merged[0]?.source).toBe('model');
  });
});

describe('placeholders from a safer rewrite', () => {
  it('are never reported as sensitive, even if the model flags them', () => {
    const text = 'Hi, I am [PERSON_1] and I take [MEDICATION_1]. Mail me at jo@example.com';
    const spans = findingsToSpans(text, [
      { text: 'PERSON_1', category: 'PERSON_NAME', tier: 1 },
      { text: '[MEDICATION_1]', category: 'MEDICATION', tier: 2 },
      { text: 'MEDICATION_1', category: 'EMAIL', tier: 2 },
    ]);
    expect(spans).toHaveLength(0);
  });
});

describe('logging helpers for regex spans', () => {
  it('maps regex types to categories and tiers', () => {
    const [ssn] = detectRegex('my ssn is 527-61-3849');
    expect(categoryOf(ssn!)).toBe('GOV_ID');
    expect(tierOf(ssn!)).toBe(3);
    const [mail] = detectRegex('mail a.b@example.com');
    expect(categoryOf(mail!)).toBe('EMAIL');
    expect(tierOf(mail!)).toBe(2);
  });
});

describe('persona values used in the mock chat', () => {
  it('regex layer catches the structured ones (names, conditions and IDs need the model)', () => {
    const text =
      'phone (865) 555-0142, mail maya.okafor@example.com, card 4539 1488 0343 6467, ssn 527-61-3849, ' +
      'other ssn 486-72-1905, key sk-live-9fK2mQx7RtB4vLw8Zd3NpY6a';
    const types = detectRegex(text).map((s) => s.type).sort();
    expect(types).toEqual(['API_KEY', 'CARD', 'EMAIL', 'PHONE', 'SSN', 'SSN']);
  });
});
