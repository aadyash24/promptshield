import { findEditable, rangesFor, readEditable, replaceEditableText, type Reading } from '../lib/dom';
import type { AnalyzeResponse, RewriteResponse, SpansUpdate } from '../lib/messages';
import type { Span } from '../lib/types';
import { WarningUI } from '../lib/ui';

const DEBOUNCE_MS = 300;
const MIN_CHARS = 4;

export default defineContentScript({
  matches: ['*://chatgpt.com/*', '*://claude.ai/*', '*://gemini.google.com/*'],
  main() {
    // Privacy rule: prompt text is never logged and never stored. It only passes through memory.
    let timer: number | undefined;
    let seq = 0;
    let target: HTMLElement | null = null;
    let reading: Reading | null = null;
    let spans: Span[] = [];
    let dismissedSig = '';

    const ui = new WarningUI({
      onRewrite: () => void rewrite(),
      onIgnore: () => {
        dismissedSig = signature(spans);
        clearAll();
      },
      onReplace: (text) => {
        if (target) replaceEditableText(target, text);
        ui.hideCard();
      },
      onBack: () => {
        if (target && spans.length) ui.showFound(target, spans);
      },
    });

    const signature = (s: Span[]) => s.map((x) => `${x.type}:${x.start}-${x.end}`).join('|');

    function clearAll() {
      ui.clearHighlights();
      ui.hideCard();
    }

    function analyze(el: HTMLElement) {
      if (!el.isConnected) {
        clearAll();
        return;
      }
      const r = readEditable(el);
      if (r.text.trim().length < MIN_CHARS) {
        target = null;
        spans = [];
        clearAll();
        return;
      }
      target = el;
      reading = r;
      const id = ++seq;
      chrome.runtime
        .sendMessage({ type: 'analyze', id, text: r.text })
        .then((res: AnalyzeResponse | undefined) => {
          if (res && res.id === seq) apply(res.spans);
        })
        .catch(() => {});
    }

    function apply(next: Span[]) {
      if (!target) return;
      // Skip if the user kept typing since this analysis started. A fresh one is coming.
      const now = readEditable(target);
      if (!reading || now.text !== reading.text) return;

      spans = next;
      if (spans.length === 0) {
        clearAll();
        return;
      }
      if (signature(spans) === dismissedSig) return;
      dismissedSig = '';
      ui.setHighlights(now.segments ? rangesFor(now.segments, spans) : []);
      ui.showFound(target, spans);
    }

    async function rewrite() {
      if (!target) return;
      const el = target;
      ui.showWorking(el);
      try {
        const res = (await chrome.runtime.sendMessage({
          type: 'rewrite',
          text: reading?.text ?? '',
          spans,
        })) as RewriteResponse;
        ui.showResult(el, res.text, res.usedModel, res.error);
      } catch (err) {
        ui.showResult(el, '', false, String(err));
      }
    }

    document.addEventListener(
      'input',
      (e) => {
        if (ui.owns(e.target)) return;
        const el = findEditable(e.target);
        if (!el) return;
        window.clearTimeout(timer);
        timer = window.setTimeout(() => analyze(el), DEBOUNCE_MS);
      },
      true,
    );

    // Slower contextual detector results arrive here.
    chrome.runtime.onMessage.addListener((msg: SpansUpdate) => {
      if (msg?.type === 'spans' && msg.id === seq) apply(msg.spans);
    });

    window.addEventListener('resize', () => ui.place());
    window.addEventListener('scroll', () => ui.place(), true);
  },
});
