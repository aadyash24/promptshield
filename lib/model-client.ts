import { typeForCategory, type Span } from './types';

/** Local server started with: python finetune/serve.py (see finetune/README.md). */
export const SERVER = 'http://127.0.0.1:8765';

export interface Finding {
  text: string;
  category: string;
  tier?: number;
}

/**
 * The model returns the sensitive text, not offsets. Find every place that text
 * appears in the prompt. Unknown categories are kept as OTHER so nothing is dropped.
 */
export function findingsToSpans(prompt: string, findings: Finding[]): Span[] {
  const spans: Span[] = [];
  const seen = new Set<string>();
  for (const f of findings) {
    if (!f || typeof f.text !== 'string' || f.text.length < 2) continue;
    const category = typeof f.category === 'string' ? f.category : 'OTHER';
    const tier = f.tier === 1 || f.tier === 2 || f.tier === 3 ? f.tier : undefined;
    let from = 0;
    for (;;) {
      const at = prompt.indexOf(f.text, from);
      if (at < 0) break;
      const key = `${at}:${at + f.text.length}`;
      if (!seen.has(key)) {
        seen.add(key);
        spans.push({
          start: at,
          end: at + f.text.length,
          type: typeForCategory(category),
          text: f.text,
          source: 'model',
          category,
          tier,
        });
      }
      from = at + f.text.length;
    }
  }
  return spans;
}

let latestCheck: AbortController | null = null;

/**
 * Ask the local server for findings. With supersede, a newer live check cancels the one still
 * running, so checking every 60 ms never builds a queue of stale requests.
 */
export async function detectViaServer(text: string, timeoutMs = 20000, supersede = false): Promise<Span[]> {
  const ctl = new AbortController();
  if (supersede) {
    latestCheck?.abort();
    latestCheck = ctl;
  }
  const timer = setTimeout(() => ctl.abort(), timeoutMs);
  try {
    const res = await fetch(`${SERVER}/detect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
      signal: ctl.signal,
    });
    if (!res.ok) return [];
    const data = (await res.json()) as { findings?: Finding[] };
    return findingsToSpans(text, data.findings ?? []);
  } catch {
    return []; // server not running: regex layer still works
  } finally {
    clearTimeout(timer);
    if (latestCheck === ctl) latestCheck = null;
  }
}
