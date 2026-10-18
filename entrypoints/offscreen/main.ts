import { CreateMLCEngine, type MLCEngine } from '@mlc-ai/web-llm';
import { REWRITE_SYSTEM_PROMPT } from '../../lib/rewrite';
import type { OffscreenRequest, OffscreenResponse } from '../../lib/messages';

// Qwen3 rewrites the prompt. DistilBERT (the local server) does the detecting.
// To try the smaller, faster model, change this one line to 'Qwen3-0.6B-q4f16_1-MLC'.
const MODEL_ID = 'Qwen3-1.7B-q4f16_1-MLC';

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
    // Qwen3 "thinks" out loud by default. Turn that off so the reply is only the rewritten message.
    extra_body: { enable_thinking: false },
  });
  return reply.choices[0]?.message?.content ?? '';
}

chrome.runtime.onMessage.addListener(
  (msg: OffscreenRequest, _sender, sendResponse: (r: OffscreenResponse) => void) => {
    if (msg?.target !== 'offscreen') return false;

    if (msg.type === 'llm-rewrite') {
      rewrite(msg.masked)
        .then((text) => sendResponse({ ok: true, text }))
        .catch((err) => sendResponse({ ok: false, error: String(err) }));
      return true;
    }

    return false;
  },
);
