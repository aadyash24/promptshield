import { detectRegex } from './regex';

export const REWRITE_SYSTEM_PROMPT =
  'You rewrite messages so they can be sent to a chatbot without private details. ' +
  'In the message, private details were already replaced by general wording such as "a medical condition", "my doctor" or "my email address". ' +
  'Rewrite it so it reads naturally and still asks for exactly the same help. ' +
  'Keep the general wording. Never add names, numbers, dates, places or any other specific detail, and never guess what was removed. ' +
  'Output only the rewritten message.';

export interface SafeResult {
  text: string;
  /** True when the model's wording was accepted, false when we fell back to the plain placeholder text. */
  usedModel: boolean;
}

function clean(output: string): string {
  let t = output.trim();
  // Drop a leading "Here is the rewritten message:" style line.
  const lines = t.split('\n');
  if (lines.length > 1 && /^here('|’)?s?\b.*:\s*$/i.test((lines[0] ?? '').trim())) {
    t = lines.slice(1).join('\n').trim();
  }
  // Drop wrapping quotes.
  if (t.length > 1 && /^["“].*["”]$/s.test(t)) t = t.slice(1, -1).trim();
  return t;
}

/**
 * Accept the model's rewrite only if it is provably clean. Otherwise return the
 * deterministic placeholder version, so a small model can never leak a detail.
 */
export function safeRewrite(
  masked: string,
  originals: string[],
  modelOutput: string | null,
): SafeResult {
  const fallback: SafeResult = { text: masked, usedModel: false };
  if (!modelOutput) return fallback;

  const out = clean(modelOutput);
  if (!out) return fallback;
  if (out.length > masked.length * 3 + 200) return fallback;

  const lower = out.toLowerCase();
  for (const o of originals) {
    if (o.length >= 3 && lower.includes(o.toLowerCase())) return fallback;
  }
  if (detectRegex(out).length > 0) return fallback;

  return { text: out, usedModel: true };
}
