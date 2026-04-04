/**
 * Recently viewed courses (localStorage, max 10).
 */

(function () {
  "use strict";

  const STORAGE_KEY = "tcf_recent_courses";
  const MAX_ENTRIES = 10;

  function isSafeCourseHref(href) {
    if (typeof href !== "string" || !href) {
      return false;
    }
    try {
      const u = new URL(href, window.location.origin);
      return (
        u.origin === window.location.origin && u.pathname.startsWith("/course/")
      );
    } catch {
      return false;
    }
  }

  function normalizeEntry(raw) {
    if (!raw || typeof raw !== "object") {
      return null;
    }
    const href = raw.href;
    const code = typeof raw.code === "string" ? raw.code.trim() : "";
    const title = typeof raw.title === "string" ? raw.title.trim() : "";
    if (!isSafeCourseHref(href) || !code) {
      return null;
    }
    const at =
      typeof raw.at === "number" && Number.isFinite(raw.at)
        ? raw.at
        : Date.now();
    return { href, code, title, at };
  }

  function readRaw() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return [];
      }
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  function list() {
    const normalized = [];
    for (const item of readRaw()) {
      const n = normalizeEntry(item);
      if (n) {
        normalized.push(n);
      }
    }
    normalized.sort((a, b) => b.at - a.at);
    const seen = new Set();
    const out = [];
    for (const n of normalized) {
      if (!seen.has(n.href)) {
        seen.add(n.href);
        out.push(n);
        if (out.length >= MAX_ENTRIES) {
          break;
        }
      }
    }
    return out;
  }

  function write(entries) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  }

  function record({ href, code, title }) {
    const next = normalizeEntry({
      href,
      code,
      title: title || "",
      at: Date.now(),
    });
    if (!next) {
      return;
    }
    const existing = list().filter((e) => e.href !== next.href);
    write([next, ...existing].slice(0, MAX_ENTRIES));
    window.dispatchEvent(new CustomEvent("tcfRecentCoursesChange"));
  }

  function fillDropdown(root) {
    const listEl = root.querySelector("[data-recent-courses-list]");
    const emptyEl = root.querySelector("[data-recent-courses-empty]");
    if (!listEl || !emptyEl) {
      return;
    }
    listEl.textContent = "";
    const items = list();
    if (items.length === 0) {
      emptyEl.hidden = false;
      listEl.hidden = true;
      return;
    }
    emptyEl.hidden = true;
    listEl.hidden = false;
    for (const entry of items) {
      const a = document.createElement("a");
      a.href = entry.href;
      a.className = "dropdown__item recent-courses__item";
      const code = document.createElement("span");
      code.className = "recent-courses__code";
      code.textContent = entry.code;
      a.appendChild(code);
      if (entry.title) {
        const title = document.createElement("span");
        title.className = "recent-courses__title";
        title.textContent = entry.title;
        a.appendChild(title);
      }
      listEl.appendChild(a);
    }
  }

  function initRecentCoursesDropdown() {
    const root = document.getElementById("recentCoursesDropdown");
    if (!root) {
      return;
    }
    const trigger = root.querySelector("[data-recent-courses-trigger]");
    function refresh() {
      fillDropdown(root);
    }
    refresh();
    window.addEventListener("storage", function (e) {
      if (e.key === STORAGE_KEY) {
        refresh();
      }
    });
    window.addEventListener("tcfRecentCoursesChange", refresh);
    if (trigger) {
      trigger.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        const open = !root.classList.contains("is-open");
        root.classList.toggle("is-open", open);
        trigger.setAttribute("aria-expanded", open ? "true" : "false");
        if (open) {
          refresh();
        }
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initRecentCoursesDropdown);
  } else {
    initRecentCoursesDropdown();
  }

  window.tcfRecentCourses = {
    list,
    record,
    isSafeCourseHref,
  };
})();
