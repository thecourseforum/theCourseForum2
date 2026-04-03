/**
 * Small helpers for GET partial HTML (browse / schedule builder).
 */
(function (global) {
  global.TcfPartialHtml = {
    /**
     * @param {string} url
     * @param {{ signal?: AbortSignal, headers?: Record<string, string> }} [opts]
     */
    fetchHtml: function fetchHtml(url, opts) {
      opts = opts || {};
      const headers = Object.assign(
        {
          Accept: "text/html",
          "X-Requested-With": "XMLHttpRequest",
        },
        opts.headers || {},
      );
      return fetch(url, {
        method: "GET",
        credentials: "same-origin",
        headers: headers,
        signal: opts.signal,
      });
    },

    /**
     * @param {HTMLElement | null} el
     * @param {string} html
     */
    replaceInner: function replaceInner(el, html) {
      if (el) {
        el.innerHTML = html;
      }
    },
  };
})(window);
