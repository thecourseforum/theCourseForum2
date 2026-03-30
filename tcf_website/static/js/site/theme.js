/**
 * Theme Toggle
 * ============
 * Handles light/dark mode switching with localStorage persistence.
 */

(function () {
  "use strict";

  const STORAGE_KEY = "theme";
  const THEMES = ["light", "dark"];

  /**
   * Get the current theme from localStorage.
   * Defaults to 'light' if not set.
   */
  function getTheme() {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored && THEMES.includes(stored) ? stored : "light";
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
  function setTheme(theme) {
    if (!THEMES.includes(theme)) return;
    applyTheme(theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }

  /**
   * Toggle between light and dark themes.
   */
  function toggleTheme() {
    const current = getTheme();
    const newTheme = current === "dark" ? "light" : "dark";
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

  function initializeTheme() {
    applyTheme(getTheme());
  }

  // Initialize on DOM ready or immediate if already loaded
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      initializeTheme();
      initThemeToggle();
    });
  } else {
    initializeTheme();
    initThemeToggle();
  }

  // Expose API globally
  window.theme = {
    get: getTheme,
    set: setTheme,
    toggle: toggleTheme,
  };
})();
