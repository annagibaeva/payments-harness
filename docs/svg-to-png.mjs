// One-off: rasterize architecture.svg -> architecture.png at 2x for crispness.
// Usage: node docs/svg-to-png.mjs
import { readFileSync, writeFileSync } from 'node:fs';
import { Resvg } from '@resvg/resvg-js';

const svg = readFileSync(new URL('./architecture.svg', import.meta.url), 'utf8');
const resvg = new Resvg(svg, {
  fitTo: { mode: 'width', value: 1920 },           // 2x the 960 viewBox
  font: { loadSystemFonts: true },
  background: '#F8FAFC',
});
const png = resvg.render().asPng();
writeFileSync(new URL('./architecture.png', import.meta.url), png);
console.log(`wrote architecture.png (${png.length} bytes)`);
