import { mergeSpans } from './regex';
import type { PiiType, Span } from './types';

/**
 * Contextual PII detector (names, addresses, organizations) using GLiNER in the browser.
 *
 * STATUS: wired but NOT yet verified end to end. It was written from the `gliner` npm
 * package README and has not been run against a real browser GPU. The detection owner
 * must confirm the three constants below. If anything fails, this adapter reports an error
 * and the extension keeps working with the regex detector alone.
 *
 * TODO(detection owner):
 *  1. Confirm the exact ONNX file name in the model repo (a quantized file is best).
 *  2. Bundle the onnxruntime-web .wasm files into the extension (MV3 forbids remote scripts)
 *     and point WASM_PATHS at them, e.g. copy them to public/ort/ and use chrome.runtime.getURL('ort/').
 *  3. Tune LABELS and THRESHOLD against the 20 test prompts.
 */
const TOKENIZER_ID = 'onnx-community/gliner_multi_pii-v1';
const MODEL_URL =
  'https://huggingface.co/onnx-community/gliner_multi_pii-v1/resolve/main/onnx/model_quantized.onnx';
const WASM_PATHS: string | undefined = undefined; // TODO: local path, see note 2
const THRESHOLD = 0.5;

const LABELS: Record<string, PiiType> = {
  person: 'PERSON',
  'street address': 'ADDRESS',
  organization: 'ORG',
};

type GlinerInstance = {
  initialize(): Promise<void>;
  inference(args: {
    texts: string[];
    entities: string[];
    flatNer?: boolean;
    threshold?: number;
  }): Promise<{ spanText: string; start: number; end: number; label: string; score: number }[][]>;
};

let instance: Promise<GlinerInstance> | null = null;

function load(): Promise<GlinerInstance> {
  if (!instance) {
    instance = (async () => {
      // Dynamic import keeps a GLiNER problem from breaking the rest of the extension.
      const { Gliner } = (await import('gliner')) as unknown as {
        Gliner: new (opts: unknown) => GlinerInstance;
      };
      const g = new Gliner({
        tokenizerPath: TOKENIZER_ID,
        onnxSettings: {
          modelPath: MODEL_URL,
          executionProvider: 'wasm',
          wasmPaths: WASM_PATHS,
          multiThread: false,
        },
        transformersSettings: { allowLocalModels: false, useBrowserCache: true },
        maxWidth: 12,
      });
      await g.initialize();
      return g;
    })();
    // Allow a retry on the next call if loading failed.
    instance.catch(() => {
      instance = null;
    });
  }
  return instance;
}

export async function glinerSpans(text: string): Promise<Span[]> {
  const g = await load();
  const [found] = await g.inference({
    texts: [text],
    entities: Object.keys(LABELS),
    flatNer: false,
    threshold: THRESHOLD,
  });
  const spans: Span[] = (found ?? []).flatMap((e) => {
    const type = LABELS[e.label];
    return type
      ? [{ start: e.start, end: e.end, type, text: e.spanText, source: 'gliner' as const }]
      : [];
  });
  return mergeSpans(spans);
}
