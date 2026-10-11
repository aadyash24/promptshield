import { defineConfig } from 'wxt';

export default defineConfig({
  manifest: {
    name: 'Privacy Warning',
    description:
      'Warns you before sensitive info goes into an AI chatbot prompt and offers a safer rewrite. Everything runs locally in your browser.',
    // Nothing is stored, so no "storage" permission. "offscreen" hosts the local models.
    permissions: ['offscreen'],
    content_security_policy: {
      extension_pages: "script-src 'self' 'wasm-unsafe-eval'; object-src 'self';",
    },
  },
});
