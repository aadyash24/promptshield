import { CreateMLCEngine, type MLCEngine } from '@mlc-ai/web-llm';
import { glinerSpans } from '../../lib/gliner-adapter';
import { REWRITE_SYSTEM_PROMPT } from '../../lib/rewrite';
import type { OffscreenRequest, OffscreenResponse } from '../../lib/messages';

// Change this one line after the Oct 13 bake-off if Qwen wins.
const MODEL_ID = 'Llama-3.2-1B-Instruct-q4f16_1-MLC';

let engine: Promise<MLCEngine> | null = null;

function getEngine(): Promise<MLCEngine> {
  if (!engine) {
    engine = CreateMLCEngine(MODEL_ID);
    engine.catch(() => {
      engine = null; // allow a retry
    });
  }
  return engine;
}

async function rewrite(masked: string): Promise<string> {
  const e = await getEngine();
  const reply = await e.chat.completions.create({
    messages: [
      { role: 'system', content: REWRITE_SYSTEM_PROMPT },
      { role: 'user', content: masked },
    ],
    temperature: 0.2,
    max_tokens: 400,
  });
  return reply.choices[0]?.message?.content ?? '';
}

chrome.runtime.onMessage.addListener(
  (msg: OffscreenRequest, _sender, sendResponse: (r: OffscreenResponse) => void) => {
    if (msg?.target !== 'offscreen') return false;

    if (msg.type === 'gliner') {
      glinerSpans(msg.text)
        .then((spans) => sendResponse({ ok: true, spans }))
        .catch((err) => sendResponse({ ok: false, error: String(err) }));
      return true;
    }

    if (msg.type === 'llm-rewrite') {
      rewrite(msg.masked)
        .then((text) => sendResponse({ ok: true, text }))
        .catch((err) => sendResponse({ ok: false, error: String(err) }));
      return true;
    }

    return false;
  },
);
