import { describe, expect, it } from 'vitest';
import { detectRegex } from '../lib/regex';
import { maskText } from '../lib/mask';
import { safeRewrite } from '../lib/rewrite';

const prompt = 'Email jane@example.com or call 865-555-0142, then email jane@example.com again.';

describe('maskText', () => {
  it('swaps spans for general wording and reuses it for repeats', () => {
    const { masked, entries } = maskText(prompt, detectRegex(prompt));
    expect(masked).toBe('Email my email address or call my phone number, then email my email address again.');
    expect(entries.map((e) => e.placeholder)).toEqual(['my email address', 'my phone number']);
  });

  it('says "another" for a second different value of the same kind', () => {
    const text = 'Write to a@example.com and b@example.com.';
    expect(maskText(text, detectRegex(text)).masked).toBe('Write to my email address and another email address.');
  });

  it('uses the detector category, such as a medical condition', () => {
    const text = 'I was diagnosed with type 2 diabetes last year.';
    const start = text.indexOf('type 2 diabetes');
    const span = { start, end: start + 'type 2 diabetes'.length, type: 'OTHER' as const, text: 'type 2 diabetes', source: 'model' as const, category: 'MED_CONDITION' };
    expect(maskText(text, [span]).masked).toBe('I was diagnosed with a medical condition last year.');
  });

  it('returns the text unchanged when nothing was found', () => {
    const text = 'How do I sort a list?';
    expect(maskText(text, []).masked).toBe(text);
  });
});

describe('safeRewrite', () => {
  const { masked, entries } = maskText(prompt, detectRegex(prompt));
  const originals = entries.map((e) => e.original);

  it('accepts a clean model rewrite', () => {
    const out = 'Please contact my email address or my phone number, and follow up by email.';
    expect(safeRewrite(masked, originals, out)).toEqual({ text: out, usedModel: true });
  });

  it('falls back when the model leaks an original value', () => {
    const out = 'Please contact jane@example.com or my phone number.';
    expect(safeRewrite(masked, originals, out)).toEqual({ text: masked, usedModel: false });
  });

  it('falls back when the model invents a new sensitive value', () => {
    const out = 'Please contact my email address or 555-123-4567.';
    expect(safeRewrite(masked, originals, out)).toEqual({ text: masked, usedModel: false });
  });

  it('falls back on empty or missing output', () => {
    expect(safeRewrite(masked, originals, '')).toEqual({ text: masked, usedModel: false });
    expect(safeRewrite(masked, originals, null)).toEqual({ text: masked, usedModel: false });
  });

  it('falls back on runaway output', () => {
    const out = 'blah '.repeat(500);
    expect(safeRewrite(masked, originals, out).usedModel).toBe(false);
  });

  it('strips a chatty lead-in line and wrapping quotes', () => {
    const out = 'Here is the rewritten message:\n"Please contact my email address."';
    expect(safeRewrite(masked, originals, out)).toEqual({
      text: 'Please contact my email address.',
      usedModel: true,
    });
  });
});
