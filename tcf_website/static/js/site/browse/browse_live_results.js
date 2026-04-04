/**
 * Live refresh of advanced browse search results (HTML partial) without full reload.
 */
(function () {
  const DEBOUNCE_MS = 300;
  const CHANGE_FLUSH_MS = 50;

  const DEBOUNCED_NAMES = new Set([
    "title",
    "course_number",
    "description",
    "instructor",
    "units_min",
    "units_max",
    "min_gpa",
    "component",
    "club_name",
  ]);

  const form = document.querySelector(
    ".advanced-search[data-browse-live-results]",
  );
  const resultsRoot = document.getElementById("browse-advanced-results-root");
  if (!form || !resultsRoot) {
    return;
  }

  const browsePageTitle = document.title;
  const baseUrl = form.dataset.browseBaseUrl || form.action;
  const titleEl = document.getElementById("browse-header-title");
  const descEl = document.getElementById("browse-header-description");
  const catalogEl = document.getElementById("browse-default-catalog");

  let abortCtl = null;
  let debounceTimer = null;
  let changeTimer = null;

  function parseTotal(raw) {
    const num = parseInt(String(raw), 10);
    return Number.isFinite(num) ? num : 0;
  }

  function resultCountLabel(n) {
    const singular = form.dataset.browseResultLabelSingular || "course";
    const plural = form.dataset.browseResultLabelPlural || "courses";
    const noun = n === 1 ? singular : plural;
    return `${n} ${noun}`;
  }

  function updateHeader(totalRaw) {
    const n = parseTotal(totalRaw);
    if (titleEl) {
      titleEl.textContent = "Search Results";
    }
    if (descEl) {
      descEl.textContent = `${resultCountLabel(n)} found.`;
    }
    document.title = `${resultCountLabel(n)} · ${browsePageTitle}`;
  }

  function hideCatalog() {
    if (catalogEl) {
      catalogEl.hidden = true;
    }
  }

  /** GET params from the form plus any query keys only present on action (e.g. mode=clubs). */
  function searchParamsFromFormAndAction() {
    const params = new URLSearchParams(new FormData(form));
    const actionUrl = new URL(form.action, window.location.origin);
    actionUrl.searchParams.forEach((value, key) => {
      if (!params.has(key)) {
        params.set(key, value);
      }
    });
    return params;
  }

  function buildParamsForFetch() {
    const params = searchParamsFromFormAndAction();
    params.delete("page");
    params.set("partial", "results");
    return params;
  }

  function buildParamsForHistory() {
    const params = searchParamsFromFormAndAction();
    params.delete("page");
    params.delete("partial");
    const qs = params.toString();
    const u = new URL(form.action, window.location.origin);
    return qs ? `${u.pathname}?${qs}` : u.pathname;
  }

  async function refreshResults() {
    if (abortCtl) {
      abortCtl.abort();
    }
    abortCtl = new AbortController();

    const params = buildParamsForFetch();
    const fetchUrl = new URL(form.action, window.location.origin);
    fetchUrl.search = params.toString();

    resultsRoot.setAttribute("aria-busy", "true");

    function showError(message) {
      resultsRoot.innerHTML =
        '<p class="text-danger text-sm p-4" role="alert">' + message + "</p>";
    }

    try {
      const fetchOpts = { signal: abortCtl.signal };
      let res;
      if (window.TcfHttp && window.TcfHttp.fetchHtml) {
        res = await window.TcfHttp.fetchHtml(fetchUrl.toString(), fetchOpts);
      } else {
        res = await fetch(fetchUrl.toString(), {
          method: "GET",
          credentials: "same-origin",
          signal: abortCtl.signal,
          headers: {
            Accept: "text/html",
            "X-Requested-With": "XMLHttpRequest",
          },
        });
      }

      if (res.status === 204) {
        window.location.assign(baseUrl);
        return;
      }

      if (!res.ok) {
        showError("Search failed. Please try again.");
        return;
      }

      const html = await res.text();
      resultsRoot.innerHTML = html;

      const inner = resultsRoot.querySelector("[data-browse-total]");
      const totalRaw = inner ? inner.getAttribute("data-browse-total") : "0";
      updateHeader(totalRaw);
      hideCatalog();

      history.replaceState(null, "", buildParamsForHistory());
    } catch (e) {
      if (e.name !== "AbortError") {
        console.error(e);
        showError(
          "Could not load results. Check your connection and try again.",
        );
      }
    } finally {
      resultsRoot.removeAttribute("aria-busy");
    }
  }

  function scheduleRefreshDebounced() {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    debounceTimer = window.setTimeout(() => {
      debounceTimer = null;
      refreshResults();
    }, DEBOUNCE_MS);
  }

  function scheduleRefreshSoon() {
    if (changeTimer) {
      clearTimeout(changeTimer);
    }
    changeTimer = window.setTimeout(() => {
      changeTimer = null;
      refreshResults();
    }, CHANGE_FLUSH_MS);
  }

  form.addEventListener(
    "input",
    function (ev) {
      const t = ev.target;
      if (!(t instanceof HTMLElement)) {
        return;
      }
      const name = t.getAttribute("name");
      if (name && DEBOUNCED_NAMES.has(name)) {
        scheduleRefreshDebounced();
      }
    },
    true,
  );

  form.addEventListener("change", function () {
    scheduleRefreshSoon();
  });

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    if (debounceTimer) {
      clearTimeout(debounceTimer);
      debounceTimer = null;
    }
    if (changeTimer) {
      clearTimeout(changeTimer);
      changeTimer = null;
    }
    refreshResults();
  });
})();
