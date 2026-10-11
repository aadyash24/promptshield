# Privacy Warning

A Manifest V3 browser extension that warns you before a prompt containing sensitive info goes to an AI chatbot, highlights it in the text box, and offers a safer rewrite. Built for the Human Factors in Cybersecurity project.

**Privacy rules for this codebase:** everything runs in the browser, prompt text is never logged or stored, and the only network traffic is the one-time model download. There is no `storage` permission on purpose.

## Run it

```bash
npm install
npm run dev        # opens Chrome with the extension loaded and hot reload
```

Or load a build by hand: `npm run build`, open `chrome://extensions`, turn on Developer mode, click Load unpacked, and pick `.output/chrome-mv3`.

Other commands: `npm test` (unit tests), `npm run typecheck`, `npm run zip`.

Supported sites: chatgpt.com, claude.ai, gemini.google.com. Add more in `entrypoints/content.ts`.

## How it works

```
Page (AI site)            Service worker               Offscreen document
content script  <------>  regex detector     <------>  GLiNER-PII  (contextual PII)
reads prompt box          message router               WebLLM + Llama-3.2-1B (rewrite)
paints highlights         creates offscreen page
shows warning card
```

1. The content script reads the text box on a 300 ms debounce and asks the service worker to analyze it.
2. The regex detector answers instantly (emails, phones, SSNs, Luhn-checked cards, API keys, high-entropy tokens). The slower contextual detector (GLiNER) updates the page if it finds more.
3. Detections are painted with the CSS Custom Highlight API, so the page's editor DOM is never modified.
4. "Use safer version" swaps each detection for a placeholder like `[EMAIL_1]`, asks the local model to smooth the wording, then re-scans the result. If anything sensitive survives, it falls back to the plain placeholder text (`lib/rewrite.ts`). A small model can never leak a detail.

## What is verified and what is not

| Part | Status |
| --- | --- |
| Regex detector, masking, safe-rewrite fallback | Unit tested (`npm test`) |
| DOM text mapping and highlight ranges | Tested in jsdom |
| Typecheck and production build | Passing |
| Content script and warning card in a real browser | **Not yet tried.** First thing to do: `npm run dev` and type in ChatGPT |
| WebLLM rewrite on a real GPU | **Not yet tried.** Model id is in `entrypoints/offscreen/main.ts` |
| GLiNER contextual detection | **Not verified.** See the TODO in `lib/gliner-adapter.ts` |

## Open work, by owner

- **Detection owner:** finish `lib/gliner-adapter.ts` (confirm the ONNX file name, wasm paths, labels, threshold). The extension works without it, regex only.
- **Model owner:** run `bakeoff/` on Tue Oct 13 (below), then set `MODEL_ID` in `entrypoints/offscreen/main.ts`.
- **UI owner:** try the card on each site, fix selectors or replace behavior where an editor misbehaves (`lib/dom.ts`, `lib/ui.ts`). Textareas get the card but no inline highlights.
- **Demo owner:** write the 20-prompt test set (10 sensitive, 10 clean) from `tests/regex.test.ts` as a starting point, then the script and backup video.

## Model bake-off

```bash
python3 -m http.server 8080 --directory bakeoff
```

Open http://localhost:8080 in Chrome, load a model, run all 15 prompts, tick "Meaning kept" for good rewrites, and download the CSV. Do it once per model (Llama-3.2-1B and Qwen2.5-1.5B). Confirm the exact model ids against WebLLM's prebuilt model list if a load fails.

## Known limits

- The first rewrite downloads the model, which can take a while. Pre-load it before any demo.
- The build is about 40 MB because the ONNX runtime wasm files are bundled. That is fine for loading unpacked.
- `onnxruntime-web` contains a direct `eval` that the bundler warns about. Chrome's extension CSP blocks `eval`, so the GLiNER path may need a different execution provider or build. Check the offscreen page console.
- Rewrite quality of a 1B model is modest by design. The fallback keeps it safe.
