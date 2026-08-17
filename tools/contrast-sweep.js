/* Measure every text node on the rendered page against its own background.
 *
 * Written because contrast cannot be asserted from the stylesheet. A token pair
 * that reads well on the paper can fall under the floor on the tinted band two
 * rules later, and the only thing that knows which background a label actually
 * lands on is the browser that composited it. Three such pairs were found this
 * way on 2026-08-17 — the record labels at 2.55, the proof line at 4.43, and the
 * table and terminal captions at 4.29 on `--bg-2`.
 *
 * It walks both themes, composites translucent backgrounds (the sticky bar is
 * 86% paper) onto the page colour, and applies the WCAG AA floor by measured
 * pixel size: 3.0 for large text, 4.5 for everything else.
 *
 * Usage: open the page, paste into the DevTools console, read the result.
 *        Returns { under_floor, results } — `under_floor: 0` is the passing state.
 * Not in CI: it needs a real browser with the real fonts loaded. The static
 * assertions live in tools/check-pack.py.
 */

(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));

  const parse = s => {
    let m = s.match(/color\(srgb\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)(?:\s*\/\s*([\d.]+))?\)/);
    if (m) return { rgb: [+m[1] * 255, +m[2] * 255, +m[3] * 255], a: m[4] === undefined ? 1 : +m[4] };
    m = s.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const v = m[1].split(/[,\s/]+/).filter(Boolean).map(Number);
    return { rgb: v.slice(0, 3), a: v.length > 3 ? v[3] : 1 };
  };
  const over = (fg, bg) => fg.rgb.map((c, i) => c * fg.a + bg[i] * (1 - fg.a));
  const lin = c => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
  const L = a => 0.2126 * lin(a[0]) + 0.7152 * lin(a[1]) + 0.0722 * lin(a[2]);
  const ratio = (a, b) => { const [x, y] = [L(a), L(b)].sort((p, q) => q - p); return +((x + 0.05) / (y + 0.05)).toFixed(2); };

  const results = [];
  const restore = document.documentElement.dataset.theme;

  for (const theme of ['light', 'dark']) {
    document.documentElement.dataset.theme = theme;
    await sleep(400);                       // background transitions settle, or every card reads as its old colour
    const base = parse(getComputedStyle(document.body).backgroundColor).rgb;
    const bgOf = el => {
      let n = el;
      while (n && n !== document.documentElement) {
        const c = parse(getComputedStyle(n).backgroundColor);
        if (c && c.a > 0) return over(c, base);
        n = n.parentElement;
      }
      return base;
    };

    const seen = new Set();
    for (const el of document.querySelectorAll('body *')) {
      const ownText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
      if (!ownText) continue;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) continue;
      const fg = parse(cs.color);
      if (!fg) continue;
      const bg = bgOf(el);
      const r = ratio(over(fg, bg), bg);
      const px = parseFloat(cs.fontSize);
      const floor = (px >= 24 || (px >= 18.66 && +cs.fontWeight >= 700)) ? 3 : 4.5;
      const key = theme + '|' + el.className + '|' + el.tagName;
      if (r < floor && !seen.has(key)) {
        seen.add(key);
        results.push({
          theme, r, floor, px: +px.toFixed(1),
          sel: el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ').join('.') : ''),
          text: el.textContent.trim().slice(0, 40),
        });
      }
    }
  }

  document.documentElement.dataset.theme = restore;
  return { under_floor: results.length, results };
})();
