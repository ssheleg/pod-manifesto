/* Proof of Done — podmanifesto.org
   No dependencies, no scroll listener. Everything here is progressive: the
   document reads completely with JavaScript disabled. */

(function () {
  'use strict';

  var root = document.documentElement;

  /* ── theme ───────────────────────────────────────────────────────────── */

  var STORE = 'pod-theme';

  // Light is this document's default register; dark is a choice the reader
  // makes and it is remembered. The system preference does not decide.
  function systemTheme() { return 'light'; }

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
    // Read the paper colour from the pack's token layer rather than repeating it.
    meta.setAttribute('content',
      getComputedStyle(root).getPropertyValue('--bg').trim() || '#f4f4ef');
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

      // The label changes, not only the colour — a colour-only confirmation is
      // invisible to a third of the people this page is for.
      function done(ok) {
        btn.textContent = ok ? 'copied' : 'select + copy';
        btn.setAttribute('data-done', ok ? '1' : '0');
        window.setTimeout(function () {
          btn.textContent = original;
          btn.removeAttribute('data-done');
        }, 1800);
      }

      // clipboard.writeText can stay pending when the document is not focused,
      // so the async path is raced against a timeout that falls back.
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

  /* ── boot: the masthead assembles once, the frame draws itself ───────── */
  /* Why does this move: a founding document should read as issued, not pasted.
     It runs once per load and never on a repeated path. */

  var reducedBoot = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var boot = document.querySelector('.boot');
  if (boot) {
    if (reducedBoot) boot.classList.add('is-up');
    else window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () { boot.classList.add('is-up'); });
    });
  }

  /* ── reveal on entry ─────────────────────────────────────────────────── */
  /* Why does this move: a section arriving with no transition reads as a cut.
     It runs once per section, never on a repeated path, and reduced motion
     resolves it to the final state without ever hiding content. */

  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var reveals = Array.prototype.slice.call(document.querySelectorAll('.reveal'));

  if (!reveals.length) {
    /* nothing to do */
  } else if (reduced || !('IntersectionObserver' in window)) {
    reveals.forEach(function (el) { el.classList.add('is-in'); });
  } else {
    var revealer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        revealer.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.02 });
    reveals.forEach(function (el) { revealer.observe(el); });
  }

  /* ── the index marks the section being read ──────────────────────────── */

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

    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) { visible[entry.target.id] = entry.isIntersecting; });

      // The furthest-scrolled visible section wins, so a long section that is
      // still partly in the band does not keep the previous entry highlighted.
      var activeId = null;
      for (var i = targets.length - 1; i >= 0; i--) {
        if (visible[targets[i].id]) { activeId = targets[i].id; break; }
      }
      if (!activeId) return;

      links.forEach(function (a) { a.classList.remove('is-active'); });
      if (byId[activeId]) byId[activeId].classList.add('is-active');
    }, { rootMargin: '-12% 0px -70% 0px', threshold: 0 });

    targets.forEach(function (el) { spy.observe(el); });
  }

  /* ── the contents panel: open on wide screens, collapsed on narrow ───── */

  var wrap = document.querySelector('.toc__wrap');
  if (wrap) {
    var wide = window.matchMedia('(min-width: 64rem)');
    var sync = function (mq) {
      if (mq.matches) wrap.setAttribute('open', '');
      else wrap.removeAttribute('open');
    };
    sync(wide);
    if (wide.addEventListener) wide.addEventListener('change', sync);
    else if (wide.addListener) wide.addListener(sync);

    wrap.addEventListener('click', function (e) {
      var a = e.target.closest ? e.target.closest('a') : null;
      if (a && !wide.matches) wrap.removeAttribute('open');
    });
  }
})();
