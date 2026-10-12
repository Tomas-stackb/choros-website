/* Choros — site behaviour: nav, dropdown, reveal, booking embed. No dependencies. */
(function () {
  var docEl = document.documentElement;
  docEl.classList.add('js');

  /* Mobile menu */
  var burger = document.querySelector('.burger');
  if (burger) {
    burger.addEventListener('click', function () {
      var open = docEl.classList.toggle('nav-open');
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.querySelectorAll('.nav-mobile a').forEach(function (a) {
      a.addEventListener('click', function () {
        docEl.classList.remove('nav-open');
        burger.setAttribute('aria-expanded', 'false');
      });
    });
  }

  /* Solutions dropdown (click for touch; hover handled in CSS) */
  document.querySelectorAll('.nav-drop').forEach(function (drop) {
    var btn = drop.querySelector('button');
    if (!btn) return;
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var isOpen = drop.hasAttribute('data-open');
      document.querySelectorAll('.nav-drop[data-open]').forEach(function (d) {
        d.removeAttribute('data-open');
        var b = d.querySelector('button');
        if (b) b.setAttribute('aria-expanded', 'false');
      });
      if (!isOpen) {
        drop.setAttribute('data-open', '');
        btn.setAttribute('aria-expanded', 'true');
      }
    });
  });
  document.addEventListener('click', function () {
    document.querySelectorAll('.nav-drop[data-open]').forEach(function (d) {
      d.removeAttribute('data-open');
      var b = d.querySelector('button');
      if (b) b.setAttribute('aria-expanded', 'false');
    });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      docEl.classList.remove('nav-open');
      if (burger) burger.setAttribute('aria-expanded', 'false');
      document.querySelectorAll('.nav-drop[data-open]').forEach(function (d) {
        d.removeAttribute('data-open');
      });
    }
  });

  /* Reveal on scroll */
  var revealEls = document.querySelectorAll('.reveal');
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduced || !('IntersectionObserver' in window)) {
    revealEls.forEach(function (el) { el.classList.add('in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('in');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revealEls.forEach(function (el) { io.observe(el); });
  }

  /* Stagger siblings marked with data-stagger on a parent */
  document.querySelectorAll('[data-stagger]').forEach(function (parent) {
    var kids = parent.querySelectorAll(':scope > .reveal');
    kids.forEach(function (kid, i) {
      kid.style.setProperty('--d', (i * 90) + 'ms');
    });
  });

  /* Booking calendar: the third-party embed loads when asked for, not on page load */
  document.querySelectorAll('[data-booking]').forEach(function (box) {
    var btn = box.querySelector('[data-booking-load]');
    if (!btn) return;
    var warmed = false;
    function warm() {
      if (warmed) return;
      warmed = true;
      var l = document.createElement('link');
      l.rel = 'preconnect';
      l.href = new URL(box.getAttribute('data-booking-src')).origin;
      document.head.appendChild(l);
    }
    function load() {
      var f = document.createElement('iframe');
      f.src = box.getAttribute('data-booking-src');
      f.id = box.getAttribute('data-booking-id');
      f.title = 'Book a call with Choros';
      f.setAttribute('allow', 'payment');
      f.setAttribute('scrolling', 'no');
      f.style.cssText = 'width:100%;border:none;overflow:hidden';
      box.replaceWith(f);
      var s = document.createElement('script');
      s.src = 'https://link.msgsndr.com/js/form_embed.js';
      s.async = true;
      document.body.appendChild(s);
    }
    ['pointerenter', 'focus', 'touchstart'].forEach(function (ev) {
      btn.addEventListener(ev, warm, { once: true, passive: true });
    });
    btn.addEventListener('click', load, { once: true });
  });

  /* Footer year */
  document.querySelectorAll('[data-year]').forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });
})();
