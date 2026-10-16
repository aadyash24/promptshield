import { defineConfig } from 'wxt';

export default defineConfig({
  manifest: {
    name: 'Privacy Warning',
    description:
      'Warns you before sensitive info goes into an AI chatbot prompt and offers a safer rewrite. Everything runs locally in your browser.',
    // Nothing is stored, so no "storage" permission. "offscreen" hosts the local models.
    permissions: ['offscreen'],
    // The fine-tuned detector runs in a local server on this computer (finetune/serve.py).
    host_permissions: ['http://127.0.0.1:8765/*'],
    content_security_policy: {
      extension_pages: "script-src 'self' 'wasm-unsafe-eval'; object-src 'self';",
    },
  },
});
