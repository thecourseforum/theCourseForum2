/**
 * Shared XHR helpers: cookie read and fetch with consistent headers.
 */
(function (global) {
  function getCookie(name) {
    const prefix = name + "=";
    const parts = (document.cookie || "").split(";");
    for (let i = 0; i < parts.length; i++) {
      const p = parts[i].trim();
      if (p.indexOf(prefix) === 0) {
        return decodeURIComponent(p.slice(prefix.length));
      }
    }
    return "";
  }

  /**
   * @param {string} url
   * @param {{ signal?: AbortSignal, headers?: Record<string, string>, method?: string, body?: BodyInit }} [opts]
   */
  function fetchHtml(url, opts) {
    opts = opts || {};
    const headers = Object.assign(
      {
        Accept: "text/html",
        "X-Requested-With": "XMLHttpRequest",
      },
      opts.headers || {},
    );
    return fetch(url, {
      method: opts.method || "GET",
      credentials: "same-origin",
      headers,
      signal: opts.signal,
      body: opts.body,
    });
  }

  /**
   * @param {string} url
   * @param {{ signal?: AbortSignal, headers?: Record<string, string>, method?: string, body?: BodyInit, csrfToken?: string }} [opts]
   */
  function fetchJson(url, opts) {
    opts = opts || {};
    const headers = Object.assign(
      {
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      opts.headers || {},
    );
    const token = opts.csrfToken;
    if (token) {
      headers["X-CSRFToken"] = token;
    }
    return fetch(url, {
      method: opts.method || "GET",
      credentials: "same-origin",
      headers,
      signal: opts.signal,
      body: opts.body,
    });
  }

  global.TcfHttp = {
    getCookie,
    fetchHtml,
    fetchJson,
  };
})(window);
