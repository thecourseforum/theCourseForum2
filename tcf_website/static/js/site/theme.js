/**
 * Theme Toggle
 * ============
 * Handles light/dark mode switching with localStorage persistence.
 */

(function () {
  "use strict";

  const STORAGE_KEY = "theme";
  const USER_SET_KEY = "theme-user-set";
  const THEMES = ["light", "dark"];

  /**
   * Get the current theme from localStorage or system preference.
   */
  function getTheme() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && THEMES.includes(stored)) {
      return stored;
    }
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  /**
   * Apply theme to the document and notify listeners.
   */
  function applyTheme(theme) {
    if (!THEMES.includes(theme)) return;
    document.documentElement.setAttribute("data-theme", theme);
    window.dispatchEvent(new CustomEvent("themechange", { detail: { theme } }));
  }

  /**
   * Set the theme on the document and persist to localStorage.
   */
  function setTheme(theme, persist = true) {
    if (!THEMES.includes(theme)) return;

    applyTheme(theme);
    if (persist) {
      localStorage.setItem(STORAGE_KEY, theme);
      return;
    }
    localStorage.removeItem(STORAGE_KEY);
  }

  /**
   * Toggle between light and dark themes.
   */
  function toggleTheme() {
    const current = getTheme();
    const newTheme = current === "dark" ? "light" : "dark";
    localStorage.setItem(USER_SET_KEY, "1");
    setTheme(newTheme);
  }

  /**
   * Initialize theme toggle buttons.
   */
  function initThemeToggle() {
    const toggleButtons = document.querySelectorAll("[data-theme-toggle]");

    toggleButtons.forEach((button) => {
      button.addEventListener("click", (e) => {
        e.preventDefault();
        toggleTheme();
      });
    });
  }

  /**
   * Listen for system preference changes.
   */
  function initSystemPreferenceListener() {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    mediaQuery.addEventListener("change", (e) => {
      if (!localStorage.getItem(USER_SET_KEY)) {
        setTheme(e.matches ? "dark" : "light", false);
      }
    });
  }

  function initializeThemeState() {
    if (
      localStorage.getItem(STORAGE_KEY) &&
      !localStorage.getItem(USER_SET_KEY)
    ) {
      // Preserve existing explicit user choices from before USER_SET_KEY existed.
      localStorage.setItem(USER_SET_KEY, "1");
    }
    applyTheme(getTheme());
  }

  // Initialize on DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      initializeThemeState();
      initThemeToggle();
      initSystemPreferenceListener();
    });
  } else {
    initializeThemeState();
    initThemeToggle();
    initSystemPreferenceListener();
  }

  // Expose API globally
  window.theme = {
    get: getTheme,
    set: setTheme,
    toggle: toggleTheme,
  };
})();
