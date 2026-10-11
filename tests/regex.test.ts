import { describe, expect, it } from 'vitest';
import { detectRegex, luhn } from '../lib/regex';

const types = (text: string) => detectRegex(text).map((s) => s.type);

describe('regex detector: sensitive prompts', () => {
  it('flags an email address', () => {
    expect(types('Write to jane.doe@example.com about the lease')).toEqual(['EMAIL']);
  });

  it('flags US phone numbers in common formats', () => {
    expect(types('Call me at (865) 555-0142')).toEqual(['PHONE']);
    expect(types('My number is 865-555-0142')).toEqual(['PHONE']);
    expect(types('Text +1 865 555 0142 please')).toEqual(['PHONE']);
  });

  it('flags a valid SSN but not an impossible one', () => {
    expect(types('My SSN is 123-45-6789')).toEqual(['SSN']);
    expect(types('Part number 000-12-3456')).toEqual([]);
    expect(types('Code 987-65-4321')).toEqual([]);
  });

  it('flags a card number only when it passes the Luhn check', () => {
    expect(types('Card 4111 1111 1111 1111 expires soon')).toEqual(['CARD']);
    expect(types('Card 4111 1111 1111 1112 expires soon')).toEqual([]);
  });

  it('flags known API key formats', () => {
    expect(types('key AKIAIOSFODNN7EXAMPLE')).toEqual(['API_KEY']);
    expect(types('token ghp_' + 'a1B2c3D4e5'.repeat(4))).toEqual(['API_KEY']);
    expect(types('use sk-' + 'Ab3dE6gH9jK2mN5pQ8sT1vX4zC7')).toEqual(['API_KEY']);
  });

  it('flags a long high-entropy token', () => {
    expect(types('secret=Zk9Qx3LmP7vR2tYb8NwC4hJd6FsA1eGu0XoI5')).toEqual(['API_KEY']);
  });

  it('does not double flag a card as a phone number', () => {
    expect(types('4111111111111111')).toEqual(['CARD']);
  });

  it('reports exact character offsets', () => {
    const text = 'Email jane@example.com now';
    const span = detectRegex(text)[0]!;
    expect(text.slice(span.start, span.end)).toBe('jane@example.com');
  });
});

describe('regex detector: clean prompts', () => {
  const clean = [
    'How do I sort a list of dictionaries in Python?',
    'Explain the difference between TCP and UDP.',
    'Summarize the causes of the French Revolution in three bullets.',
    'What is a good name for a bakery?',
    'Write a haiku about autumn leaves.',
    'Translate "good morning" into Spanish and German.',
    'Why is the sky blue at noon but red at sunset?',
    'Compare React and Vue for a small team project.',
    'The meeting is on 2026-10-20 at 3 pm.',
    'Version 3.14.159 shipped in build 20261011.',
  ];
  for (const prompt of clean) {
    it(`leaves "${prompt.slice(0, 40)}" alone`, () => {
      expect(detectRegex(prompt)).toEqual([]);
    });
  }
});

describe('luhn', () => {
  it('accepts a known good test number', () => {
    expect(luhn('4111111111111111')).toBe(true);
  });
  it('rejects wrong length and non-digits', () => {
    expect(luhn('411111')).toBe(false);
    expect(luhn('4111abcd11111111')).toBe(false);
  });
});
