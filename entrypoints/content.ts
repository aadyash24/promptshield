import { findEditable, rangesFor, readEditable, replaceEditableText, type Reading } from '../lib/dom';
import type {
  AnalyzeResponse,
  CondResponse,
  DetectFullResponse,
  RewriteResponse,
  SpansUpdate,
  StudyEvent,
} from '../lib/messages';
import { categoryOf, tierOf, type Span } from '../lib/types';
import { WarningUI } from '../lib/ui';

const DEBOUNCE_MS = 300;
const MIN_CHARS = 4;

export default defineContentScript({
  matches: [
    '*://chatgpt.com/*',
    '*://claude.ai/*',
    '*://gemini.google.com/*',
    // Mock chat used in the user study, served by finetune/serve.py.
    'http://127.0.0.1:8765/mock/*',
  ],
  main() {
    // Privacy rule: prompt text is never logged and never stored. It only passes through memory.
    let timer: number | undefined;
    let seq = 0;
    let target: HTMLElement | null = null;
    let reading: Reading | null = null;
    let spans: Span[] = [];
    let dismissedSig = '';

    // Study mode (mock chat only). Logs events, never prompt text or detected values.
    const study = location.origin === 'http://127.0.0.1:8765' && location.pathname.startsWith('/mock');
    const q = new URLSearchParams(location.search);
    const pid = (q.get('pid') ?? 'unknown').replace(/[^A-Za-z0-9_-]/g, '').slice(0, 32) || 'unknown';
    // The condition is assigned by the local server so participants never see it in the URL.
    // ?cond= is only a manual override for testing.
    let cond: 'active' | 'silent' = q.get('cond') === 'silent' ? 'silent' : 'active';
    let silent = study && cond === 'silent';
    const condReady: Promise<void> =
      study && !q.get('cond')
        ? chrome.runtime
            .sendMessage({ type: 'get-cond', pid })
            .then((r: CondResponse | undefined) => {
              if (r?.cond) {
                cond = r.cond;
                silent = cond === 'silent';
              }
            })
            .catch(() => {})
        : Promise.resolve();
    let cardVisible = false;
    let loggedDetectSig = '';
    let loggedShownSig = '';

    function log(event: StudyEvent['event'], extra: Partial<StudyEvent> = {}) {
      if (!study) return;
      const started = Number(document.body.dataset.taskStart ?? 0);
      const e: StudyEvent = {
        pid,
        cond,
        task: document.body.dataset.task ?? '',
        event,
        ms: started ? Date.now() - started : undefined,
        ...extra,
      };
      void chrome.runtime.sendMessage({ type: 'log', event: e }).catch(() => {});
    }

    function summarize(list: Span[]) {
      return {
        n: list.length,
        categories: [...new Set(list.map(categoryOf))].sort(),
        max_tier: list.reduce((m, s) => Math.max(m, tierOf(s)), 0),
      };
    }

    const ui = new WarningUI({
      onRewrite: () => {
        log('rewrite_clicked');
        void rewrite();
      },
      onIgnore: () => {
        log('warning_ignored');
        dismissedSig = signature(spans);
        clearAll();
      },
      onReplace: (text) => {
        log('rewrite_applied');
        if (target) replaceEditableText(target, text);
        ui.hideCard();
        cardVisible = false;
      },
      onBack: () => {
        if (target && spans.length) ui.showFound(target, spans);
      },
    });

    const signature = (s: Span[]) => s.map((x) => `${x.type}:${x.start}-${x.end}`).join('|');

    function clearAll() {
      ui.clearHighlights();
      ui.hideCard();
      cardVisible = false;
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
      if (study) {
        const sum = summarize(spans);
        const sig = `${sum.categories.join(',')}:${sum.n}`;
        if (sig !== loggedDetectSig) {
          loggedDetectSig = sig;
          log('detected', sum);
        }
      }
      if (silent) return; // silent condition: detect and log, but show nothing
      if (signature(spans) === dismissedSig) return;
      dismissedSig = '';
      ui.setHighlights(now.segments ? rangesFor(now.segments, spans) : []);
      ui.showFound(target, spans);
      cardVisible = true;
      if (study) {
        const sum = summarize(spans);
        const sig = `${sum.categories.join(',')}:${sum.n}`;
        if (sig !== loggedShownSig) {
          loggedShownSig = sig;
          log('warning_shown', sum);
        }
      }
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

    if (study) {
      void condReady.then(() => log('session_start'));
      document.addEventListener('pw:task', () => {
        loggedDetectSig = '';
        loggedShownSig = '';
        dismissedSig = '';
        void condReady.then(() => log('task_start'));
      });
      // The mock page fires pw:send before it clears the box, so the text is still readable here.
      document.addEventListener('pw:send', () => {
        const box = document.getElementById('prompt');
        const warned = cardVisible && !silent;
        const text = box ? readEditable(box).text : '';
        clearAll();
        void chrome.runtime
          .sendMessage({ type: 'detect-full', text })
          .then((res: DetectFullResponse | undefined) => {
            const found = res?.spans ?? [];
            log('send', { ...summarize(found), disclosed: found.length > 0, warned });
          })
          .catch(() => log('send', { n: 0, disclosed: false, warned }));
      });
    }

    // Slower contextual detector results arrive here.
    chrome.runtime.onMessage.addListener((msg: SpansUpdate) => {
      if (msg?.type === 'spans' && msg.id === seq) apply(msg.spans);
    });

    window.addEventListener('resize', () => ui.place());
    window.addEventListener('scroll', () => ui.place(), true);
  },
});
