import { CATEGORY_LABEL, DOMAIN_LABEL, DOMAIN_ORDER, TIER_NAME, TYPE_LABEL, domainOf, tierOf, type Domain, type Span } from './types';

const HIGHLIGHT_NAME = 'privacy-warning';

const PAGE_CSS = `
::highlight(${HIGHLIGHT_NAME}) {
  background-color: rgba(255, 196, 0, 0.35);
  text-decoration: underline wavy #d93025;
  text-decoration-skip-ink: none;
}`;

const CARD_CSS = `
:host { all: initial; }
.card {
  position: fixed; z-index: 2147483647; width: 320px; box-sizing: border-box;
  padding: 14px 16px; border-radius: 12px; background: #ffffff; color: #1f1f1f;
  border: 1px solid #d0d0d0; box-shadow: 0 6px 24px rgba(0,0,0,.18);
  font: 14px/1.4 system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
}
@media (prefers-color-scheme: dark) {
  .card { background: #2b2b2b; color: #f0f0f0; border-color: #555; }
  .preview { background: #1f1f1f; border-color: #555; }
  button.secondary { color: #f0f0f0; border-color: #666; }
}
h2 { margin: 0 0 6px; font-size: 14px; font-weight: 600; }
p { margin: 0 0 8px; }
ul { margin: 0 0 10px; padding-left: 18px; }
.note { font-size: 12px; opacity: .8; }
.preview {
  max-height: 140px; overflow: auto; white-space: pre-wrap; word-break: break-word;
  padding: 8px; margin: 0 0 8px; border: 1px solid #ccc; border-radius: 8px; background: #f7f7f7;
  user-select: text;
}
.row { display: flex; gap: 8px; flex-wrap: wrap; }
button {
  font: inherit; font-weight: 600; padding: 6px 12px; border-radius: 8px; cursor: pointer;
  border: 1px solid transparent; background: #1a73e8; color: #fff;
}
button.secondary { background: transparent; color: #1f1f1f; border-color: #bbb; }
button:disabled { opacity: .6; cursor: default; }
button:focus-visible { outline: 2px solid #1a73e8; outline-offset: 2px; }
`;

function sheet(css: string): CSSStyleSheet {
  const s = new CSSStyleSheet();
  s.replaceSync(css);
  return s;
}

function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  props: { text?: string; className?: string } = {},
  ...children: (Node | string)[]
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (props.text !== undefined) node.textContent = props.text;
  if (props.className) node.className = props.className;
  for (const c of children) node.append(c);
  return node;
}

export interface CardActions {
  onRewrite: () => void;
  onIgnore: () => void;
  onReplace: (text: string) => void;
  onBack: () => void;
}

export class WarningUI {
  private host: HTMLElement | null = null;
  private root: ShadowRoot | null = null;
  private card: HTMLElement | null = null;
  private pageSheet: CSSStyleSheet | null = null;
  private anchor: HTMLElement | null = null;

  constructor(private actions: CardActions) {}

  /** True if the event target is inside our own card. */
  owns(target: EventTarget | null): boolean {
    return !!this.host && target instanceof Node && this.host.contains(target);
  }

  // Highlights -------------------------------------------------------------

  setHighlights(ranges: Range[]): void {
    const css = CSS as unknown as { highlights?: Map<string, unknown> };
    const HighlightCtor = (window as unknown as { Highlight?: new (...r: Range[]) => unknown }).Highlight;
    if (!css.highlights || !HighlightCtor) return; // browser too old, card still works
    if (!this.pageSheet) {
      this.pageSheet = sheet(PAGE_CSS);
      document.adoptedStyleSheets = [...document.adoptedStyleSheets, this.pageSheet];
    }
    if (ranges.length === 0) css.highlights.delete(HIGHLIGHT_NAME);
    else css.highlights.set(HIGHLIGHT_NAME, new HighlightCtor(...ranges));
  }

  clearHighlights(): void {
    this.setHighlights([]);
  }

  // Card -------------------------------------------------------------------

  private ensureCard(anchor: HTMLElement): HTMLElement {
    this.anchor = anchor;
    if (!this.host) {
      this.host = document.createElement('div');
      this.root = this.host.attachShadow({ mode: 'closed' });
      this.root.adoptedStyleSheets = [sheet(CARD_CSS)];
      this.card = el('div', { className: 'card' });
      this.card.setAttribute('role', 'dialog');
      this.card.setAttribute('aria-label', 'Privacy warning');
      this.root.append(this.card);
      document.documentElement.append(this.host);
    }
    this.place();
    return this.card!;
  }

  /** Keep the card just above the text box. */
  place(): void {
    if (!this.card || !this.anchor) return;
    const r = this.anchor.getBoundingClientRect();
    this.card.style.bottom = `${Math.max(8, window.innerHeight - r.top + 8)}px`;
    this.card.style.right = `${Math.max(8, window.innerWidth - r.right)}px`;
  }

  hideCard(): void {
    this.host?.remove();
    this.host = null;
    this.root = null;
    this.card = null;
  }

  showFound(anchor: HTMLElement, spans: Span[]): void {
    const card = this.ensureCard(anchor);
    // Group by type of info first, then show the tier of each item inside its type.
    const groups = new Map<Domain, Map<string, number>>();
    for (const s of spans) {
      const label = `${(s.category && CATEGORY_LABEL[s.category]) || TYPE_LABEL[s.type]} (${TIER_NAME[tierOf(s)]})`;
      const g = groups.get(domainOf(s)) ?? new Map<string, number>();
      g.set(label, (g.get(label) ?? 0) + 1);
      groups.set(domainOf(s), g);
    }

    const list = el('div');
    for (const d of DOMAIN_ORDER) {
      const g = groups.get(d);
      if (!g) continue;
      const ul = el('ul');
      for (const [label, n] of g) ul.append(el('li', { text: n > 1 ? `${label} x${n}` : label }));
      list.append(el('h2', { text: DOMAIN_LABEL[d] }), ul);
    }
    const rewrite = el('button', { text: 'Use safer version' });
    rewrite.addEventListener('click', () => this.actions.onRewrite());
    const ignore = el('button', { text: 'Ignore', className: 'secondary' });
    ignore.addEventListener('click', () => this.actions.onIgnore());

    card.replaceChildren(
      el('h2', { text: 'This prompt may contain sensitive info' }),
      list,
      el('div', { className: 'row' }, rewrite, ignore),
      el('p', { className: 'note', text: 'Checked on your device. Nothing was sent anywhere.' }),
    );
  }

  showWorking(anchor: HTMLElement): void {
    const card = this.ensureCard(anchor);
    const busy = el('button', { text: 'Working…' });
    busy.disabled = true;
    card.replaceChildren(
      el('h2', { text: 'Writing a safer version' }),
      el('p', {
        className: 'note',
        text: 'The first time, a small model downloads to your browser. That can take a minute. It runs only on your device.',
      }),
      el('div', { className: 'row' }, busy),
    );
  }

  showResult(anchor: HTMLElement, text: string, usedModel: boolean, error?: string): void {
    const card = this.ensureCard(anchor);
    const replace = el('button', { text: 'Replace my text' });
    replace.addEventListener('click', () => this.actions.onReplace(text));
    const copy = el('button', { text: 'Copy', className: 'secondary' });
    copy.addEventListener('click', () => {
      void navigator.clipboard.writeText(text).then(() => (copy.textContent = 'Copied'));
    });
    const back = el('button', { text: 'Back', className: 'secondary' });
    back.addEventListener('click', () => this.actions.onBack());

    const note = usedModel
      ? 'Rewritten on your device. Review it before sending.'
      : 'Placeholders only. The local model was unavailable or its wording was not safe enough to use.';

    card.replaceChildren(
      el('h2', { text: 'Safer version' }),
      el('div', { className: 'preview', text }),
      el('p', { className: 'note', text: error && !usedModel ? `${note} (${error.slice(0, 80)})` : note }),
      el('div', { className: 'row' }, replace, copy, back),
    );
  }
}
