/* Admin dashboard interactions */
(function () {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const root = document.documentElement;

  // theme
  $$("[data-theme-toggle]").forEach((btn) => btn.addEventListener("click", () => {
    const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (e) { /* ignore */ }
  }));

  // sidebar (mobile)
  const sidebar = $("#sidebar"), backdrop = $(".sidebar-backdrop"), toggle = $("[data-sidebar-toggle]");
  const setSidebar = (open) => {
    if (!sidebar) return;
    sidebar.classList.toggle("is-open", open);
    backdrop && backdrop.classList.toggle("is-open", open);
    toggle && toggle.setAttribute("aria-expanded", String(open));
  };
  toggle && toggle.addEventListener("click", () => setSidebar(!sidebar.classList.contains("is-open")));
  backdrop && backdrop.addEventListener("click", () => setSidebar(false));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") setSidebar(false); });

  // confirm before destructive actions (forms with data-confirm)
  document.addEventListener("submit", (e) => {
    const form = e.target;
    if (form.matches("[data-confirm]") && !window.confirm(form.dataset.confirm)) e.preventDefault();
  }, true);

  // toasts
  $$(".toast").forEach((toast, i) => {
    const close = () => { toast.classList.add("is-leaving"); setTimeout(() => toast.remove(), 300); };
    $(".toast-close", toast)?.addEventListener("click", close);
    setTimeout(() => toast.isConnected && close(), 5000 + i * 500);
  });

  // single image preview
  $$("input[type=file][data-preview]").forEach((input) => {
    input.addEventListener("change", () => {
      const file = input.files && input.files[0];
      const box = input.closest(".image-field")?.querySelector(".image-preview");
      if (!file || !box || !file.type.startsWith("image/")) return;
      const img = document.createElement("img");
      img.src = URL.createObjectURL(file);
      img.alt = "";
      box.replaceChildren(img);
    });
  });

  // multiple image previews + drag state
  $$("input[type=file][data-multi-preview]").forEach((input) => {
    const zone = input.closest(".dropzone");
    const holder = zone?.parentElement.querySelector("[data-previews]");
    input.addEventListener("change", () => {
      if (!holder) return;
      holder.replaceChildren(...Array.from(input.files).filter((f) => f.type.startsWith("image/")).map((f) => {
        const img = document.createElement("img");
        img.src = URL.createObjectURL(f); img.alt = f.name; img.title = f.name;
        return img;
      }));
    });
    if (zone) {
      ["dragenter", "dragover"].forEach((ev) => zone.addEventListener(ev, () => zone.classList.add("is-dragover")));
      ["dragleave", "drop"].forEach((ev) => zone.addEventListener(ev, () => zone.classList.remove("is-dragover")));
    }
  });

  // password visibility
  $$("[data-pw-toggle]").forEach((btn) => btn.addEventListener("click", () => {
    const input = btn.parentElement.querySelector("input");
    input.type = input.type === "password" ? "text" : "password";
  }));
})();
