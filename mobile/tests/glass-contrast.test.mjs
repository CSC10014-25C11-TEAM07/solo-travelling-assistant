import assert from 'node:assert/strict';
import test from 'node:test';
import { palette, paneOpacity } from '../src/components/glass/colors.ts';

const rgb = hex => [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16) / 255);
const luminance = channels => channels.map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4).reduce((sum, v, i) => sum + v * [.2126, .7152, .0722][i], 0);
const contrast = (a, b) => (Math.max(a, b) + .05) / (Math.min(a, b) + .05);

test('the main pane transmits at least 40% of the scene before its edge highlight', () => {
  assert.ok(paneOpacity <= .6);
});

test('secondary text meets AA even with the glass pane over a black photograph', () => {
  const dimmestPane = rgb(palette.foam).map(channel => channel * paneOpacity);
  assert.ok(contrast(luminance(dimmestPane), luminance(rgb(palette.slate))) >= 4.5);
});

test('primary and error labels meet AA without relying on shadows', () => {
  for (const ink of [palette.pine, palette.oxide]) {
    assert.ok(contrast(luminance(rgb(ink)), luminance(rgb(palette.foam))) >= 4.5);
  }
});
