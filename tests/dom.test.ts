// @vitest-environment jsdom
import { describe, expect, it } from 'vitest';
import { rangesFor, readEditable } from '../lib/dom';
import { detectRegex } from '../lib/regex';

function editor(html: string): HTMLElement {
  const el = document.createElement('div');
  el.setAttribute('contenteditable', 'true');
  el.innerHTML = html;
  document.body.append(el);
  return el;
}

describe('readEditable and rangesFor', () => {
  it('reads paragraphs separated by newlines', () => {
    const el = editor('<p>first line</p><p>second line</p>');
    expect(readEditable(el).text).toBe('first line\nsecond line');
  });

  it('maps a detection inside one paragraph back to the exact DOM text', () => {
    const el = editor('<p>hello there</p><p>mail jane@example.com today</p>');
    const { text, segments } = readEditable(el);
    const spans = detectRegex(text);
    expect(spans).toHaveLength(1);
    const ranges = rangesFor(segments!, spans);
    expect(ranges).toHaveLength(1);
    expect(ranges[0]!.toString()).toBe('jane@example.com');
  });

  it('maps a detection that sits after inline formatting', () => {
    const el = editor('<p>call <b>me</b> at 865-555-0142 soon</p>');
    const { text, segments } = readEditable(el);
    const ranges = rangesFor(segments!, detectRegex(text));
    expect(ranges.map((r) => r.toString())).toEqual(['865-555-0142']);
  });

  it('reads a textarea value directly', () => {
    const ta = document.createElement('textarea');
    ta.value = 'my email is jane@example.com';
    expect(readEditable(ta)).toEqual({ text: 'my email is jane@example.com' });
  });
});
