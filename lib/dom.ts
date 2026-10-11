import type { Span } from './types';

export interface Segment {
  node: Text;
  start: number;
  end: number;
}

export interface Reading {
  text: string;
  /** Present for contenteditable editors. Maps text offsets back to DOM text nodes. */
  segments?: Segment[];
}

const BLOCKS = 'p,div,li,h1,h2,h3,h4,h5,h6,pre,blockquote';

export function findEditable(target: EventTarget | null): HTMLElement | null {
  if (!(target instanceof Element)) return null;
  return target.closest<HTMLElement>('textarea, [contenteditable="true"], [contenteditable="plaintext-only"]');
}

/**
 * Read the prompt text without modifying the page's editor.
 * Text nodes in different blocks are separated by a newline, and the same
 * layout is used to map detections back onto DOM ranges.
 */
export function readEditable(el: HTMLElement): Reading {
  if (el instanceof HTMLTextAreaElement) return { text: el.value };

  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  const segments: Segment[] = [];
  let text = '';
  let prevBlock: Element | null = null;
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const node = n as Text;
    const block = node.parentElement?.closest(BLOCKS) ?? el;
    if (prevBlock && block !== prevBlock) text += '\n';
    const start = text.length;
    text += node.data;
    segments.push({ node, start, end: text.length });
    prevBlock = block;
  }
  return { text, segments };
}

/** Turn detections into DOM ranges for the CSS Custom Highlight API. */
export function rangesFor(segments: Segment[], spans: Span[]): Range[] {
  const ranges: Range[] = [];
  for (const s of spans) {
    const a = segments.find((g) => s.start >= g.start && s.start < g.end);
    const b = segments.find((g) => s.end > g.start && s.end <= g.end);
    if (!a || !b) continue;
    try {
      const r = document.createRange();
      r.setStart(a.node, s.start - a.start);
      r.setEnd(b.node, s.end - b.start);
      ranges.push(r);
    } catch {
      // The editor re-rendered under us. A fresh analysis is already on its way.
    }
  }
  return ranges;
}

/** Replace the prompt with new text in a way editors such as ProseMirror accept. */
export function replaceEditableText(el: HTMLElement, text: string): void {
  if (el instanceof HTMLTextAreaElement) {
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')?.set;
    setter?.call(el, text);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    return;
  }
  el.focus();
  const sel = window.getSelection();
  if (!sel) return;
  const range = document.createRange();
  range.selectNodeContents(el);
  sel.removeAllRanges();
  sel.addRange(range);
  document.execCommand('insertText', false, text);
}
