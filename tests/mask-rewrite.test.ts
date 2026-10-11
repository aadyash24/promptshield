import { describe, expect, it } from 'vitest';
import { detectRegex } from '../lib/regex';
import { maskText } from '../lib/mask';
import { safeRewrite } from '../lib/rewrite';

const prompt = 'Email jane@example.com or call 865-555-0142, then email jane@example.com again.';

describe('maskText', () => {
  it('swaps spans for numbered placeholders and reuses them for repeats', () => {
    const { masked, entries } = maskText(prompt, detectRegex(prompt));
    expect(masked).toBe('Email [EMAIL_1] or call [PHONE_1], then email [EMAIL_1] again.');
    expect(entries.map((e) => e.placeholder)).toEqual(['[EMAIL_1]', '[PHONE_1]']);
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
    const out = 'Please contact [EMAIL_1] or [PHONE_1], and follow up by email.';
    expect(safeRewrite(masked, originals, out)).toEqual({ text: out, usedModel: true });
  });

  it('falls back when the model leaks an original value', () => {
    const out = 'Please contact jane@example.com or [PHONE_1].';
    expect(safeRewrite(masked, originals, out)).toEqual({ text: masked, usedModel: false });
  });

  it('falls back when the model invents a new sensitive value', () => {
    const out = 'Please contact [EMAIL_1] or 555-123-4567.';
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
    const out = 'Here is the rewritten message:\n"Please contact [EMAIL_1]."';
    expect(safeRewrite(masked, originals, out)).toEqual({
      text: 'Please contact [EMAIL_1].',
      usedModel: true,
    });
  });
});
