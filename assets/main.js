/* Proof of Done — podmanifesto.org
   No dependencies. Everything here is progressive: the document reads fine
   with JavaScript disabled. */

(function () {
  'use strict';

  var root = document.documentElement;

  /* ── theme ───────────────────────────────────────────────────────────── */

  var STORE = 'pod-theme';

  function systemTheme() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark' : 'light';
  }

  function currentTheme() {
    return root.getAttribute('data-theme') || systemTheme();
  }

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    try { localStorage.setItem(STORE, theme); } catch (e) {}
    var meta = document.querySelector('meta[name="theme-color"]:not([media])');
    if (!meta) {
      meta = document.createElement('meta');
      meta.setAttribute('name', 'theme-color');
      document.head.appendChild(meta);
    }
    meta.setAttribute('content', theme === 'dark' ? '#090b0a' : '#f4f4ef');
    var btn = document.getElementById('theme-toggle');
    if (btn) btn.setAttribute('aria-label', 'Switch to ' + (theme === 'dark' ? 'light' : 'dark') + ' theme');
  }

  var toggle = document.getElementById('theme-toggle');
  if (toggle) {
    applyTheme(currentTheme());
    toggle.addEventListener('click', function () {
      applyTheme(currentTheme() === 'dark' ? 'light' : 'dark');
    });
  }

  /* ── copy buttons ────────────────────────────────────────────────────── */

  function fallbackCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok;
  }

  Array.prototype.forEach.call(document.querySelectorAll('.copy'), function (btn) {
    var original = btn.textContent;
    btn.addEventListener('click', function () {
      var text = btn.getAttribute('data-copy') || '';

      function done(ok) {
        btn.textContent = ok ? 'copied' : 'select + copy';
        btn.setAttribute('data-done', ok ? '1' : '0');
        window.setTimeout(function () {
          btn.textContent = original;
          btn.removeAttribute('data-done');
        }, 1800);
      }

      // navigator.clipboard.writeText can stay pending when the document is not
      // focused, so the async path is raced against a timeout that falls back.
      if (navigator.clipboard && navigator.clipboard.writeText) {
        var settled = false;
        var finish = function (ok) { if (!settled) { settled = true; done(ok); } };
        window.setTimeout(function () { if (!settled) finish(fallbackCopy(text)); }, 700);
        navigator.clipboard.writeText(text).then(
          function () { finish(true); },
          function () { finish(fallbackCopy(text)); }
        );
      } else {
        done(fallbackCopy(text));
      }
    });
  });

  /* ── reading progress ────────────────────────────────────────────────── */

  var bar = document.getElementById('progress-bar');
  if (bar) {
    var ticking = false;
    var update = function () {
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      var pct = max > 0 ? (h.scrollTop || document.body.scrollTop) / max : 0;
      bar.style.width = Math.min(100, Math.max(0, pct * 100)).toFixed(2) + '%';
      ticking = false;
    };
    var onScroll = function () {
      if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });
    update();
  }

  /* ── table of contents: mark the section being read ──────────────────── */

  var links = Array.prototype.slice.call(document.querySelectorAll('.toc__list a'));
  if (links.length && 'IntersectionObserver' in window) {
    var byId = {};
    var targets = [];

    links.forEach(function (a) {
      var id = a.getAttribute('href').slice(1);
      var el = document.getElementById(id);
      if (el) { byId[id] = a; targets.push(el); }
    });

    var visible = {};

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        visible[entry.target.id] = entry.isIntersecting;
      });

      // The furthest-scrolled visible section wins, so a long section that is still
      // partly in the band does not keep the previous entry highlighted.
      var activeId = null;
      for (var i = targets.length - 1; i >= 0; i--) {
        if (visible[targets[i].id]) { activeId = targets[i].id; break; }
      }
      if (!activeId) return;

      links.forEach(function (a) { a.classList.remove('is-active'); });
      if (byId[activeId]) byId[activeId].classList.add('is-active');
    }, { rootMargin: '-15% 0px -70% 0px', threshold: 0 });

    targets.forEach(function (el) { observer.observe(el); });
  }

  /* ── contents panel: open on wide screens, collapsed on narrow ───────── */

  var wrap = document.querySelector('.toc__wrap');
  if (wrap) {
    var wide = window.matchMedia('(min-width: 1000px)');
    var sync = function (mq) { if (!mq.matches) wrap.removeAttribute('open'); else wrap.setAttribute('open', ''); };
    sync(wide);
    if (wide.addEventListener) wide.addEventListener('change', sync);
    else if (wide.addListener) wide.addListener(sync);

    // On narrow screens, close the panel after jumping to a section.
    wrap.addEventListener('click', function (e) {
      var a = e.target.closest ? e.target.closest('a') : null;
      if (a && !wide.matches) wrap.removeAttribute('open');
    });
  }
})();
