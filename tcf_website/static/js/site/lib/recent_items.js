/**
 * Recently viewed courses and clubs (localStorage, max 10 each).
 */

(function () {
  "use strict";

  const KINDS = {
    course: { storageKey: "tcf_recent_courses", pathPrefix: "/course/" },
    club: { storageKey: "tcf_recent_clubs", pathPrefix: "/club/" },
  };

  const MAX_ENTRIES = 5;
  const CHANGE_EVENT = "tcfRecentItemsChange";

  function isSafeHref(href, pathPrefix) {
    if (typeof href !== "string" || !href || !pathPrefix) {
      return false;
    }
    try {
      const u = new URL(href, window.location.origin);
      return (
        u.origin === window.location.origin && u.pathname.startsWith(pathPrefix)
      );
    } catch {
      return false;
    }
  }

  function normalizeEntry(raw, pathPrefix) {
    if (!raw || typeof raw !== "object") {
      return null;
    }
    const href = raw.href;
    const code = typeof raw.code === "string" ? raw.code.trim() : "";
    const title = typeof raw.title === "string" ? raw.title.trim() : "";
    if (!isSafeHref(href, pathPrefix) || !code) {
      return null;
    }
    const at =
      typeof raw.at === "number" && Number.isFinite(raw.at)
        ? raw.at
        : Date.now();
    return { href, code, title, at };
  }

  function readRaw(storageKey) {
    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) {
        return [];
      }
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  function listForKind(kind) {
    const cfg = KINDS[kind];
    if (!cfg) {
      return [];
    }
    const normalized = [];
    for (const item of readRaw(cfg.storageKey)) {
      const n = normalizeEntry(item, cfg.pathPrefix);
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

  function writeKind(kind, entries) {
    const cfg = KINDS[kind];
    if (!cfg) {
      return;
    }
    localStorage.setItem(cfg.storageKey, JSON.stringify(entries));
  }

  function recordKind(kind, { href, code, title }) {
    const cfg = KINDS[kind];
    if (!cfg) {
      return;
    }
    const next = normalizeEntry(
      {
        href,
        code,
        title: title || "",
        at: Date.now(),
      },
      cfg.pathPrefix,
    );
    if (!next) {
      return;
    }
    const existing = listForKind(kind).filter((e) => e.href !== next.href);
    writeKind(kind, [next, ...existing].slice(0, MAX_ENTRIES));
    window.dispatchEvent(new CustomEvent(CHANGE_EVENT));
  }

  function browseMode() {
    const m =
      document.body && document.body.getAttribute("data-recent-browse-mode");
    return m === "clubs" ? "club" : "course";
  }

  function emptyMessage(kind) {
    return kind === "club"
      ? "Visit a club page to see it here."
      : "Visit a course page to see it here.";
  }

  function fillDropdown(root) {
    const listEl = root.querySelector("[data-recent-items-list]");
    const emptyEl = root.querySelector("[data-recent-items-empty]");
    if (!listEl || !emptyEl) {
      return;
    }
    const kind = browseMode();
    listEl.textContent = "";
    emptyEl.textContent = emptyMessage(kind);
    const items = listForKind(kind);
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
      a.className = "dropdown__item recent-items__row";
      const primary = document.createElement("span");
      primary.className = "recent-items__primary";
      primary.textContent = entry.code;
      a.appendChild(primary);
      if (entry.title) {
        const sub = document.createElement("span");
        sub.className = "recent-items__secondary";
        sub.textContent = entry.title;
        a.appendChild(sub);
      }
      listEl.appendChild(a);
    }
  }

  function initRecentItemsDropdown() {
    const root = document.getElementById("recentItemsDropdown");
    if (!root) {
      return;
    }
    const trigger = root.querySelector("[data-recent-items-trigger]");
    function refresh() {
      fillDropdown(root);
    }
    refresh();
    window.addEventListener("storage", function (e) {
      if (
        e.key === KINDS.course.storageKey ||
        e.key === KINDS.club.storageKey
      ) {
        refresh();
      }
    });
    window.addEventListener(CHANGE_EVENT, refresh);
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
    document.addEventListener("DOMContentLoaded", initRecentItemsDropdown);
  } else {
    initRecentItemsDropdown();
  }

  window.tcfRecentItems = {
    recordCourse(payload) {
      recordKind("course", payload);
    },
    recordClub(payload) {
      recordKind("club", payload);
    },
  };
})();
