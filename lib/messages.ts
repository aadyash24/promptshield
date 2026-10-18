import type { Span } from './types';

/** Content script to background. */
export type ContentRequest =
  | { type: 'analyze'; id: number; text: string }
  | { type: 'rewrite'; text: string; spans: Span[] }
  /** Full pipeline (regex and model), awaited. Used when a study message is sent. */
  | { type: 'detect-full'; text: string }
  /** Study condition for a participant, assigned by the local server. */
  | { type: 'get-cond'; pid: string }
  /** Study event. Contains no prompt text, see StudyEvent. */
  | { type: 'log'; event: StudyEvent };

export type CondResponse = { cond: 'active' | 'silent' | null };
export type DetectFullResponse = { spans: Span[] };

/** Event-only study log. Never put prompt text or the detected values in here. */
export interface StudyEvent {
  pid: string;
  cond: 'active' | 'silent';
  task: string;
  event:
    | 'session_start'
    | 'task_start'
    | 'detected'
    | 'warning_shown'
    | 'rewrite_clicked'
    | 'rewrite_applied'
    | 'warning_ignored'
    | 'send';
  /** Number of sensitive items. */
  n?: number;
  /** Category names such as GOV_ID. Names only, never values. */
  categories?: string[];
  /** Highest tier among the items (1 somewhat sensitive, 2 very sensitive). */
  max_tier?: number;
  /** For 'send': did the sent message still contain sensitive items. */
  disclosed?: boolean;
  /** For 'send': was a warning visible to the participant at the moment of sending. */
  warned?: boolean;
  /** Milliseconds since the task started. */
  ms?: number;
}

export type AnalyzeResponse = { id: number; spans: Span[] };
export type RewriteResponse = { text: string; usedModel: boolean; error?: string };

/** Background to content script, sent after the slower model detector finishes. */
export type SpansUpdate = { type: 'spans'; id: number; spans: Span[] };

/** Background to offscreen document. Always carries target: 'offscreen'. */
export type OffscreenBody =
  | { type: 'llm-rewrite'; masked: string };
export type OffscreenRequest = { target: 'offscreen' } & OffscreenBody;

export type OffscreenResponse =
  | { ok: true; spans?: Span[]; text?: string }
  | { ok: false; error: string };
