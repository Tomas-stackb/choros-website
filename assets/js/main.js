/* Choros — site behaviour: menu, dropdown, booking embed, sticky bar, event stub. No dependencies. */
(function () {
  var docEl = document.documentElement;
  docEl.classList.add('js');

  /* Event stub. No analytics provider is chosen yet: define window.chorosTrack(name, props)
     to receive events. Props never contain personal data (paths only, no query strings). */
  function track(name, props) {
    if (typeof window.chorosTrack === 'function') {
      try { window.chorosTrack(name, props || {}); } catch (e) { /* never break the page */ }
    }
  }

  /* Mobile menu */
  var burger = document.querySelector('.burger');
  var menu = document.getElementById('nav-mobile');
  var behind = document.querySelectorAll('main, .site-footer, .mobile-cta');
  function setMenu(open) {
    docEl.classList.toggle('nav-open', open);
    burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    burger.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    behind.forEach(function (el) { if (open) el.setAttribute('inert', ''); else el.removeAttribute('inert'); });
    if (open) {
      var first = menu.querySelector('a');
      if (first) first.focus();
      track('menu_open', { page: location.pathname });
    }
  }
  if (burger && menu) {
    burger.addEventListener('click', function () { setMenu(!docEl.classList.contains('nav-open')); });
    menu.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { setMenu(false); });
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth > 960 && docEl.classList.contains('nav-open')) setMenu(false);
    });
  }

  /* Marketing dropdown: hover and focus are handled in CSS; the toggle serves touch and keyboard */
  function closeDrops(except) {
    document.querySelectorAll('.nav-drop[data-open]').forEach(function (d) {
      if (d === except) return;
      d.removeAttribute('data-open');
      var b = d.querySelector('.nav-drop-toggle');
      if (b) b.setAttribute('aria-expanded', 'false');
    });
  }
  document.querySelectorAll('.nav-drop').forEach(function (drop) {
    var btn = drop.querySelector('.nav-drop-toggle');
    if (!btn) return;
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var wasOpen = drop.hasAttribute('data-open');
      closeDrops();
      if (!wasOpen) {
        drop.setAttribute('data-open', '');
        btn.setAttribute('aria-expanded', 'true');
      }
    });
  });
  document.addEventListener('click', function () { closeDrops(); });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    if (docEl.classList.contains('nav-open')) {
      setMenu(false);
      if (burger) burger.focus();
    }
    var open = document.querySelector('.nav-drop[data-open]');
    if (open) {
      closeDrops();
      var t = open.querySelector('.nav-drop-toggle');
      if (t) t.focus();
    }
  });

  /* Sticky mobile bar: step aside while the page's own call to action is on screen */
  var bar = document.querySelector('.mobile-cta');
  var own = document.querySelectorAll('.hero .cta-row, .page-hero .cta-row, .cta-band .cta-row');
  if (bar && own.length && 'IntersectionObserver' in window) {
    var onScreen = new Set();
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) onScreen.add(en.target); else onScreen.delete(en.target); });
      bar.classList.toggle('mobile-cta--away', onScreen.size > 0);
    });
    own.forEach(function (el) { io.observe(el); });
  }

  /* Booking calendar: the third-party embed loads when asked for, not on page load */
  var topics = {
    audit: 'You are booking a call about the AI Operations Audit: from £4,950 fixed, delivered in two weeks.',
    software: 'You are booking a call about a software build: fixed scope, fixed price, and you own the code.',
    marketing: 'You are booking a call about marketing: tell us your trade, your patch and what a good month looks like.',
    builder: 'You are booking a call about Choros Plus: custom design and functionality, backed by our development team.'
  };
  var topic = new URLSearchParams(location.search).get('topic');
  var warmed = false;
  function warm(src) {
    if (warmed) return;
    warmed = true;
    var l = document.createElement('link');
    l.rel = 'preconnect';
    l.href = new URL(src).origin;
    document.head.appendChild(l);
  }
  document.querySelectorAll('[data-booking]').forEach(function (box) {
    var btn = box.querySelector('[data-booking-load]');
    var src = box.getAttribute('data-booking-src');
    if (!btn || !src) return;
    var line = document.getElementById('contact-topic');
    if (line && topic && Object.prototype.hasOwnProperty.call(topics, topic)) {
      line.textContent = topics[topic];
      line.hidden = false;
      warm(src); /* connection only; the calendar itself still waits for a click */
    }
    function load() {
      var f = document.createElement('iframe');
      f.src = src;
      f.id = box.getAttribute('data-booking-id');
      f.title = 'Book a call with Choros';
      f.setAttribute('allow', 'payment');
      f.setAttribute('scrolling', 'no');
      f.style.cssText = 'width:100%;border:none;overflow:hidden';
      box.replaceWith(f);
      var note = document.createElement('p');
      note.className = 'booking-fallback';
      note.innerHTML = 'Calendar not loading? Call <a href="tel:+447494913569">07494 913569</a> or email <a href="mailto:team@choros.io">team@choros.io</a>.';
      f.insertAdjacentElement('afterend', note);
      var s = document.createElement('script');
      s.src = 'https://link.msgsndr.com/js/form_embed.js';
      s.async = true;
      document.body.appendChild(s);
      track('booking_open', { page: location.pathname, topic: topic || '' });
    }
    ['pointerenter', 'focus', 'touchstart'].forEach(function (ev) {
      btn.addEventListener(ev, function () { warm(src); }, { once: true, passive: true });
    });
    btn.addEventListener('click', load, { once: true });
  });

  /* Click events for the stub above (labels and paths only) */
  document.addEventListener('click', function (e) {
    var a = e.target.closest ? e.target.closest('a') : null;
    if (!a) return;
    var h = a.getAttribute('href') || '';
    var loc = a.closest('.site-header') ? 'header' : a.closest('.nav-mobile') ? 'menu' : a.closest('.mobile-cta') ? 'sticky'
      : a.closest('.site-footer') ? 'footer' : a.closest('.cta-band') ? 'band' : a.closest('.hero, .page-hero') ? 'hero' : 'inline';
    if (h.indexOf('tel:') === 0) track('tel_click', { loc: loc, page: location.pathname });
    else if (h.indexOf('mailto:') === 0) track('email_click', { loc: loc, page: location.pathname });
    else if (a.classList.contains('btn')) track('cta_click', { label: a.textContent.trim(), href: h.split('?')[0], loc: loc, page: location.pathname });
    else if (a.host && a.host !== location.host) track('outbound', { host: a.host });
  }, true);

  /* Footer year */
  document.querySelectorAll('[data-year]').forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });
})();
