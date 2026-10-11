import { detectRegex, mergeSpans } from '../lib/regex';
import { maskText } from '../lib/mask';
import { safeRewrite } from '../lib/rewrite';
import type {
  AnalyzeResponse,
  ContentRequest,
  OffscreenBody,
  OffscreenResponse,
  RewriteResponse,
  SpansUpdate,
} from '../lib/messages';

const OFFSCREEN_URL = 'offscreen.html';

async function ensureOffscreen(): Promise<void> {
  if (await chrome.offscreen.hasDocument()) return;
  await chrome.offscreen.createDocument({
    url: OFFSCREEN_URL,
    reasons: [chrome.offscreen.Reason.WORKERS],
    justification: 'Run local PII detection and rewriting models in the browser.',
  });
}

async function askOffscreen(req: OffscreenBody): Promise<OffscreenResponse> {
  await ensureOffscreen();
  const res = (await chrome.runtime.sendMessage({ target: 'offscreen', ...req })) as
    | OffscreenResponse
    | undefined;
  return res ?? { ok: false, error: 'No response from the model page.' };
}

export default defineBackground(() => {
  chrome.runtime.onMessage.addListener((msg: ContentRequest & { target?: string }, sender, sendResponse) => {
    if (msg.target === 'offscreen') return false; // addressed to the offscreen page

    if (msg.type === 'analyze') {
      // Phase 1: instant regex result.
      const regexSpans = detectRegex(msg.text);
      const reply: AnalyzeResponse = { id: msg.id, spans: regexSpans };
      sendResponse(reply);

      // Phase 2: contextual detector. Updates the page later if it finds more.
      const tabId = sender.tab?.id;
      if (tabId !== undefined) {
        void askOffscreen({ type: 'gliner', text: msg.text }).then((res) => {
          if (!res.ok || !res.spans?.length) return;
          const merged = mergeSpans([...regexSpans, ...res.spans]);
          const update: SpansUpdate = { type: 'spans', id: msg.id, spans: merged };
          chrome.tabs.sendMessage(tabId, update).catch(() => {});
        });
      }
      return false;
    }

    if (msg.type === 'rewrite') {
      void (async () => {
        const spans = mergeSpans(msg.spans);
        const { masked, entries } = maskText(msg.text, spans);
        const originals = entries.map((e) => e.original);
        let reply: RewriteResponse;
        try {
          const res = await askOffscreen({ type: 'llm-rewrite', masked });
          const safe = safeRewrite(masked, originals, res.ok ? (res.text ?? null) : null);
          reply = { ...safe, error: res.ok ? undefined : res.error };
        } catch (err) {
          reply = { text: masked, usedModel: false, error: String(err) };
        }
        sendResponse(reply);
      })();
      return true; // keep the channel open for the async reply
    }

    return false;
  });
});
