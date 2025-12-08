import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  site: 'https://empirica.dev',
  outDir: './dist',
  build: {
    assets: 'assets'
  },
  markdown: {
    shikiConfig: {
      theme: 'dracula',
      wrap: true
    }
  }
});
