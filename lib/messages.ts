import type { Span } from './types';

/** Content script to background. */
export type ContentRequest =
  | { type: 'analyze'; id: number; text: string }
  | { type: 'rewrite'; text: string; spans: Span[] };

export type AnalyzeResponse = { id: number; spans: Span[] };
export type RewriteResponse = { text: string; usedModel: boolean; error?: string };

/** Background to content script, sent after the slower model detector finishes. */
export type SpansUpdate = { type: 'spans'; id: number; spans: Span[] };

/** Background to offscreen document. Always carries target: 'offscreen'. */
export type OffscreenBody =
  | { type: 'gliner'; text: string }
  | { type: 'llm-rewrite'; masked: string };
export type OffscreenRequest = { target: 'offscreen' } & OffscreenBody;

export type OffscreenResponse =
  | { ok: true; spans?: Span[]; text?: string }
  | { ok: false; error: string };
