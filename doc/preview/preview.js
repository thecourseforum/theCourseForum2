(function () {
  'use strict';
  const button = document.querySelector('[data-theme-toggle]');
  function updateThemeLabel() {
    if (button) button.textContent = document.documentElement.dataset.theme === 'dark' ? 'Use light theme' : 'Use dark theme';
  }
  if (button) button.addEventListener('click', function () {
    document.documentElement.dataset.theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    updateThemeLabel();
  });
  updateThemeLabel();
  const stage = document.querySelector('[data-component-demo]');
  if (stage && window.TCFComponents) window.TCFComponents.mount(stage, stage.dataset.componentDemo, document.body.dataset.assetBase || '../');
})();
