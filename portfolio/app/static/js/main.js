/* Salem Makki — Portfolio front-end interactions (no dependencies). */
(function () {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const root = document.documentElement;

  /* ---------------- Theme ---------------- */
  $$("[data-theme-toggle]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) { /* storage unavailable */ }
    });
  });

  /* ---------------- Mobile menu ---------------- */
  const menuBtn = $("[data-menu-toggle]");
  const nav = $("#main-nav");
  if (menuBtn && nav) {
    const setOpen = (open) => {
      nav.classList.toggle("is-open", open);
      menuBtn.setAttribute("aria-expanded", String(open));
    };
    menuBtn.addEventListener("click", () => setOpen(!nav.classList.contains("is-open")));
    $$("a", nav).forEach((a) => a.addEventListener("click", () => setOpen(false)));
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") setOpen(false); });
    document.addEventListener("click", (e) => {
      if (nav.classList.contains("is-open") && !nav.contains(e.target) && !menuBtn.contains(e.target)) setOpen(false);
    });
  }

  /* ---------------- Header state + scroll progress ---------------- */
  const header = $(".site-header");
  const onScroll = () => {
    const y = window.scrollY;
    header && header.classList.toggle("is-scrolled", y > 20);
    const max = document.documentElement.scrollHeight - window.innerHeight;
    root.style.setProperty("--progress", max > 0 ? Math.min(y / max, 1).toFixed(4) : 0);
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------------- Active nav link (home page) ---------------- */
  const navLinks = $$('.main-nav a[href^="#"]');
  if (navLinks.length && "IntersectionObserver" in window) {
    const map = new Map(navLinks.map((a) => [a.getAttribute("href").slice(1), a]));
    const spy = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          navLinks.forEach((a) => a.classList.remove("is-active"));
          const link = map.get(entry.target.id);
          link && link.classList.add("is-active");
        }
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    map.forEach((_, id) => { const el = document.getElementById(id); el && spy.observe(el); });
  }

  /* ---------------- Reveal on scroll ---------------- */
  const reveals = $$(".reveal");
  if (!reducedMotion && "IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) { entry.target.classList.add("is-visible"); io.unobserve(entry.target); }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    reveals.forEach((el) => io.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add("is-visible"));
  }

  /* ---------------- Typed role ---------------- */
  const typed = $(".typed[data-typed]");
  if (typed && !reducedMotion) {
    let words = [];
    try { words = JSON.parse(typed.dataset.typed).filter(Boolean); } catch (e) { words = []; }
    if (words.length) {
      let w = 0, i = words[0].length, deleting = true;
      const tick = () => {
        const word = words[w];
        typed.textContent = word.slice(0, i);
        let delay = deleting ? 35 : 75;
        if (!deleting && i === word.length) { delay = 2600; deleting = true; }
        else if (deleting && i === 0) { deleting = false; w = (w + 1) % words.length; delay = 400; }
        else { i += deleting ? -1 : 1; }
        setTimeout(tick, delay);
      };
      if (words.length > 1) setTimeout(tick, 3200);
    }
  }

  /* ---------------- Hero network canvas ---------------- */
  const canvas = $(".hero-canvas");
  if (canvas && canvas.getContext) {
    const ctx = canvas.getContext("2d");
    let w = 0, h = 0, nodes = [], raf = null, visible = true;
    const mouse = { x: -9999, y: -9999 };
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const nodeColor = () => getComputedStyle(root).getPropertyValue("--node").trim() || "120,150,255";

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      w = rect.width; h = rect.height;
      canvas.width = w * dpr; canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = Math.min(70, Math.floor((w * h) / 22000));
      nodes = Array.from({ length: count }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.35, vy: (Math.random() - 0.5) * 0.35,
        r: Math.random() * 1.6 + 0.8,
      }));
    };

    const draw = () => {
      const c = nodeColor();
      ctx.clearRect(0, 0, w, h);
      const linkDist = 130;
      for (let a = 0; a < nodes.length; a++) {
        const n = nodes[a];
        if (!reducedMotion) {
          n.x += n.vx; n.y += n.vy;
          if (n.x < 0 || n.x > w) n.vx *= -1;
          if (n.y < 0 || n.y > h) n.vy *= -1;
        }
        for (let b = a + 1; b < nodes.length; b++) {
          const m = nodes[b];
          const dx = n.x - m.x, dy = n.y - m.y, d = Math.hypot(dx, dy);
          if (d < linkDist) {
            ctx.strokeStyle = `rgba(${c},${(1 - d / linkDist) * 0.22})`;
            ctx.lineWidth = 1;
            ctx.beginPath(); ctx.moveTo(n.x, n.y); ctx.lineTo(m.x, m.y); ctx.stroke();
          }
        }
        const md = Math.hypot(n.x - mouse.x, n.y - mouse.y);
        if (md < 170) {
          ctx.strokeStyle = `rgba(${c},${(1 - md / 170) * 0.45})`;
          ctx.beginPath(); ctx.moveTo(n.x, n.y); ctx.lineTo(mouse.x, mouse.y); ctx.stroke();
        }
        ctx.fillStyle = `rgba(${c},0.75)`;
        ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2); ctx.fill();
      }
      if (!reducedMotion && visible) raf = requestAnimationFrame(draw);
    };

    resize(); draw();
    let resizeTimer;
    window.addEventListener("resize", () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(() => { resize(); if (reducedMotion) draw(); }, 150); });
    const hero = canvas.parentElement;
    hero.addEventListener("pointermove", (e) => { const r = canvas.getBoundingClientRect(); mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top; });
    hero.addEventListener("pointerleave", () => { mouse.x = mouse.y = -9999; });
    if ("IntersectionObserver" in window && !reducedMotion) {
      new IntersectionObserver(([entry]) => {
        visible = entry.isIntersecting;
        if (visible) { cancelAnimationFrame(raf); raf = requestAnimationFrame(draw); }
      }).observe(hero);
    }
  }

  /* ---------------- Avatar tilt ---------------- */
  const tilt = $("[data-tilt]");
  if (tilt && !reducedMotion && window.matchMedia("(pointer: fine)").matches) {
    const area = tilt.closest(".hero") || tilt;
    area.addEventListener("pointermove", (e) => {
      const r = tilt.getBoundingClientRect();
      const x = (e.clientX - (r.left + r.width / 2)) / r.width;
      const y = (e.clientY - (r.top + r.height / 2)) / r.height;
      tilt.style.transform = `perspective(900px) rotateY(${x * 8}deg) rotateX(${-y * 8}deg)`;
    });
    area.addEventListener("pointerleave", () => { tilt.style.transform = ""; });
  }

  /* ---------------- Toasts ---------------- */
  const dismissToast = (toast) => { toast.classList.add("is-leaving"); setTimeout(() => toast.remove(), 300); };
  $$(".toast").forEach((toast, i) => {
    $(".toast-close", toast)?.addEventListener("click", () => dismissToast(toast));
    setTimeout(() => toast.isConnected && dismissToast(toast), 6000 + i * 500);
  });

  /* ---------------- Copy e-mail ---------------- */
  $$("[data-copy]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const value = btn.dataset.copy;
      try {
        await navigator.clipboard.writeText(value);
      } catch (e) {
        const ta = document.createElement("textarea");
        ta.value = value; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0";
        document.body.appendChild(ta); ta.select(); document.execCommand("copy"); ta.remove();
      }
      const label = $(".copy-label", btn);
      const original = label ? label.textContent : "";
      btn.classList.add("is-copied");
      if (label) label.textContent = btn.dataset.copiedLabel || "✓";
      setTimeout(() => { btn.classList.remove("is-copied"); if (label) label.textContent = original; }, 2000);
    });
  });

  /* ---------------- Contact form (AJAX with graceful fallback) ---------------- */
  $$("[data-contact-form]").forEach((form) => {
    const status = $(".form-status", form);
    const button = $('button[type="submit"]', form);
    const label = $("[data-label]", button);
    const defaultLabel = label ? label.textContent : "";

    const setFieldError = (name, msg) => {
      const field = form.elements[name]?.closest(".field");
      const holder = $(`[data-error-for="${name}"]`, form);
      field && field.classList.toggle("has-error", Boolean(msg));
      if (holder) holder.textContent = msg || "";
      const input = form.elements[name];
      if (input) input.setAttribute("aria-invalid", msg ? "true" : "false");
    };

    form.addEventListener("submit", async (e) => {
      if (!window.fetch) return; // native submit fallback
      e.preventDefault();
      ["name", "email", "subject", "message"].forEach((n) => setFieldError(n, ""));
      status.className = "form-status"; status.textContent = "";
      button.disabled = true; if (label) label.textContent = form.dataset.sending;
      try {
        const res = await fetch(form.action, {
          method: "POST", body: new FormData(form),
          headers: { "X-Requested-With": "fetch", Accept: "application/json" },
          credentials: "same-origin",
        });
        const data = await res.json();
        status.textContent = data.message;
        status.classList.add(data.ok ? "is-success" : "is-error");
        if (data.ok) form.reset();
        Object.entries(data.errors || {}).forEach(([k, v]) => setFieldError(k, v));
        const firstError = $(".has-error input, .has-error textarea", form);
        firstError && firstError.focus();
      } catch (err) {
        status.textContent = form.dataset.error;
        status.classList.add("is-error");
      } finally {
        button.disabled = false; if (label) label.textContent = defaultLabel;
      }
    });
  });

  /* ---------------- Tabs (timeline) ---------------- */
  $$("[data-tabs]").forEach((tablist) => {
    const tabs = $$('[role="tab"]', tablist);
    const activate = (tab, focus) => {
      tabs.forEach((t) => {
        const selected = t === tab;
        t.setAttribute("aria-selected", String(selected));
        t.tabIndex = selected ? 0 : -1;
        const panel = document.getElementById(t.getAttribute("aria-controls"));
        if (panel) {
          panel.hidden = !selected;
          if (selected) $$(".reveal", panel).forEach((el) => el.classList.add("is-visible"));
        }
      });
      focus && tab.focus();
    };
    tabs.forEach((tab, i) => {
      tab.addEventListener("click", () => activate(tab));
      tab.addEventListener("keydown", (e) => {
        const rtl = document.dir === "rtl";
        const nextKey = rtl ? "ArrowLeft" : "ArrowRight";
        const prevKey = rtl ? "ArrowRight" : "ArrowLeft";
        if (e.key === nextKey) activate(tabs[(i + 1) % tabs.length], true);
        if (e.key === prevKey) activate(tabs[(i - 1 + tabs.length) % tabs.length], true);
      });
    });
  });

  /* ---------------- Gallery filter ---------------- */
  $$("[data-filter-group]").forEach((group) => {
    const items = $$(".gallery-item", group.parentElement);
    $$("[data-filter]", group).forEach((btn) => {
      btn.addEventListener("click", () => {
        const f = btn.dataset.filter;
        $$("[data-filter]", group).forEach((b) => { b.classList.toggle("is-active", b === btn); b.setAttribute("aria-pressed", String(b === btn)); });
        items.forEach((it) => it.classList.toggle("is-hidden", f !== "all" && it.dataset.category !== f));
      });
    });
  });

  /* ---------------- Lightbox ---------------- */
  const groups = $$("[data-lightbox-group]");
  if (groups.length) {
    const isAr = root.lang === "ar";
    const lb = document.createElement("div");
    lb.className = "lightbox";
    lb.setAttribute("role", "dialog");
    lb.setAttribute("aria-modal", "true");
    lb.setAttribute("aria-label", isAr ? "عارض الصور" : "Image viewer");
    lb.innerHTML = `
      <span class="lightbox-counter"></span>
      <img alt="">
      <p class="lightbox-caption"></p>
      <button type="button" class="lightbox-btn lightbox-close" aria-label="${isAr ? "إغلاق" : "Close"}">✕</button>
      <button type="button" class="lightbox-btn lightbox-prev" aria-label="${isAr ? "السابق" : "Previous"}">‹</button>
      <button type="button" class="lightbox-btn lightbox-next" aria-label="${isAr ? "التالي" : "Next"}">›</button>`;
    document.body.appendChild(lb);
    const img = $("img", lb), cap = $(".lightbox-caption", lb), counter = $(".lightbox-counter", lb);
    let items = [], index = 0, lastFocus = null;

    const show = (i) => {
      index = (i + items.length) % items.length;
      const a = items[index];
      img.src = a.getAttribute("href");
      img.alt = a.dataset.caption || "";
      cap.textContent = a.dataset.caption || "";
      counter.textContent = `${index + 1} / ${items.length}`;
      $(".lightbox-prev", lb).hidden = $(".lightbox-next", lb).hidden = items.length < 2;
    };
    const open = (group, a) => {
      items = $$("[data-lightbox]", group).filter((el) => !el.closest(".is-hidden"));
      lastFocus = document.activeElement;
      show(items.indexOf(a));
      lb.classList.add("is-open");
      document.body.style.overflow = "hidden";
      $(".lightbox-close", lb).focus();
    };
    const close = () => {
      lb.classList.remove("is-open");
      document.body.style.overflow = "";
      lastFocus && lastFocus.focus();
    };
    groups.forEach((group) => {
      group.addEventListener("click", (e) => {
        const a = e.target.closest("[data-lightbox]");
        if (!a) return;
        e.preventDefault();
        open(group, a);
      });
    });
    $(".lightbox-close", lb).addEventListener("click", close);
    $(".lightbox-prev", lb).addEventListener("click", () => show(index - 1));
    $(".lightbox-next", lb).addEventListener("click", () => show(index + 1));
    lb.addEventListener("click", (e) => { if (e.target === lb) close(); });
    document.addEventListener("keydown", (e) => {
      if (!lb.classList.contains("is-open")) return;
      if (e.key === "Escape") close();
      if (e.key === "ArrowRight") show(index + (document.dir === "rtl" ? -1 : 1));
      if (e.key === "ArrowLeft") show(index + (document.dir === "rtl" ? 1 : -1));
      if (e.key === "Tab") { // simple focus trap
        const f = $$("button:not([hidden])", lb);
        const first = f[0], last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });
    let touchX = null;
    lb.addEventListener("touchstart", (e) => { touchX = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener("touchend", (e) => {
      if (touchX === null) return;
      const dx = e.changedTouches[0].clientX - touchX;
      if (Math.abs(dx) > 50) show(index + (dx < 0 ? 1 : -1));
      touchX = null;
    });
  }

  /* ---------------- Footer year ---------------- */
  $$("[data-year]").forEach((el) => { el.textContent = new Date().getFullYear(); });
})();
