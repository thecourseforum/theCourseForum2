/**
 * Theme Toggle
 * ============
 * Handles light/dark mode switching with localStorage persistence.
 */

(function() {
  'use strict';

  const STORAGE_KEY = 'theme';
  const THEMES = ['light', 'dark'];

  /**
   * Get the current theme from localStorage or system preference.
   */
  function getTheme() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && THEMES.includes(stored)) {
      return stored;
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  /**
   * Set the theme on the document and persist to localStorage.
   */
  function setTheme(theme) {
    if (!THEMES.includes(theme)) return;
    
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(STORAGE_KEY, theme);
    
    // Dispatch custom event for components that need to react
    window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
  }

  /**
   * Toggle between light and dark themes.
   */
  function toggleTheme() {
    const current = getTheme();
    const newTheme = current === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
  }

  /**
   * Initialize theme toggle buttons.
   */
  function initThemeToggle() {
    const toggleButtons = document.querySelectorAll('[data-theme-toggle]');
    
    toggleButtons.forEach(button => {
      button.addEventListener('click', (e) => {
        e.preventDefault();
        toggleTheme();
      });
    });
  }

  /**
   * Listen for system preference changes.
   */
  function initSystemPreferenceListener() {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    mediaQuery.addEventListener('change', (e) => {
      // Only auto-switch if user hasn't manually set a preference
      if (!localStorage.getItem(STORAGE_KEY)) {
        setTheme(e.matches ? 'dark' : 'light');
      }
    });
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      initThemeToggle();
      initSystemPreferenceListener();
    });
  } else {
    initThemeToggle();
    initSystemPreferenceListener();
  }

  // Expose API globally
  window.theme = {
    get: getTheme,
    set: setTheme,
    toggle: toggleTheme
  };
})();
