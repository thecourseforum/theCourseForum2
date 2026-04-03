/**
 * Refresh the schedule builder grid via partial=grid.
 */
(function (global) {
  let gridRefreshGen = 0;
  let gridFetchAbort = null;

  function historyUrlWithoutPartial(urlStr) {
    const u = new URL(urlStr, window.location.origin);
    u.searchParams.delete("partial");
    const q = u.searchParams.toString();
    return q ? u.pathname + "?" + q : u.pathname;
  }

  function syncSemesterComboFromForm(form) {
    if (!form) {
      return;
    }
    const combo = form.querySelector(".combo");
    if (!combo) {
      return;
    }
    const hidden = combo.querySelector('input[type="hidden"][name="semester"]');
    const textInput = combo.querySelector(".combo__input");
    if (!hidden || !textInput || !hidden.value) {
      return;
    }
    const val = hidden.value;
    const opts = combo.querySelectorAll(".combo__option");
    for (let i = 0; i < opts.length; i++) {
      if (String(opts[i].dataset.value) === String(val)) {
        textInput.value = opts[i].textContent.trim();
        return;
      }
    }
  }

  function syncSemesterFormHiddenFromUrl(urlStr) {
    const u = new URL(urlStr, window.location.origin);
    const form = document.querySelector(".schedule-builder__semester-form");
    if (!form) {
      return;
    }
    function setOrRemoveHidden(name, value) {
      const sel = 'input[type="hidden"][name="' + name + '"]';
      const inputs = form.querySelectorAll(sel);
      if (value === null || value === "") {
        inputs.forEach(function (inp) {
          inp.remove();
        });
        return;
      }
      const first = inputs[0];
      if (first) {
        first.value = value;
        for (let i = 1; i < inputs.length; i++) {
          inputs[i].remove();
        }
      } else {
        const h = document.createElement("input");
        h.type = "hidden";
        h.name = name;
        h.value = value;
        form.appendChild(h);
      }
    }
    const semester = u.searchParams.get("semester");
    if (semester) {
      setOrRemoveHidden("semester", semester);
    }
    const sch = u.searchParams.get("schedule");
    const cmp = u.searchParams.get("compare");
    const ov = u.searchParams.get("overlap");
    if (sch) {
      setOrRemoveHidden("schedule", sch);
    } else {
      setOrRemoveHidden("schedule", null);
    }
    setOrRemoveHidden("compare", cmp || null);
    setOrRemoveHidden("overlap", ov || null);
    syncSemesterComboFromForm(form);
  }

  /**
   * @param {string} fetchUrl
   * @param {string} [historyUrl]
   * @returns {Promise<void>}
   */
  function replaceGridFromUrl(fetchUrl, historyUrl) {
    const root = document.getElementById("schedule-builder-grid-root");
    if (!root || !global.TcfPartialHtml) {
      return Promise.resolve();
    }
    const myGen = ++gridRefreshGen;
    if (gridFetchAbort) {
      gridFetchAbort.abort();
    }
    gridFetchAbort = new AbortController();
    const signal = gridFetchAbort.signal;

    const u = new URL(fetchUrl, window.location.origin);
    u.searchParams.set("partial", "grid");
    root.setAttribute("aria-busy", "true");
    const hist = historyUrl || fetchUrl;
    return global.TcfPartialHtml.fetchHtml(u.toString(), { signal })
      .then(function (res) {
        if (myGen !== gridRefreshGen) {
          return null;
        }
        if (!res.ok) {
          window.location.assign(historyUrlWithoutPartial(hist));
          return null;
        }
        return res.text();
      })
      .then(function (html) {
        if (html == null || myGen !== gridRefreshGen) {
          return;
        }
        global.TcfPartialHtml.replaceInner(root, html);
        const cleanHist = historyUrlWithoutPartial(hist);
        history.replaceState(null, "", cleanHist);
        syncSemesterFormHiddenFromUrl(cleanHist);
        if (typeof global.initSearchBarContainersIn === "function") {
          global.initSearchBarContainersIn(root);
        }
      })
      .catch(function (err) {
        if (err.name === "AbortError") {
          return;
        }
        if (myGen === gridRefreshGen) {
          window.location.assign(historyUrlWithoutPartial(hist));
        }
      })
      .finally(function () {
        if (myGen === gridRefreshGen) {
          root.removeAttribute("aria-busy");
        }
      });
  }

  global.TcfScheduleGrid = {
    replaceFromUrl: replaceGridFromUrl,
    historyUrlWithoutPartial,
  };

  /**
   * Current schedule-builder term and return URL for modals / POST next=.
   * The term combo and history stay in sync on partial grid updates; static HTML
   * templates (e.g. "New schedule") must read this instead of SSR-only values.
   */
  function activeSemesterId() {
    const form = document.querySelector(".schedule-builder__semester-form");
    if (form) {
      const inp = form.querySelector('input[type="hidden"][name="semester"]');
      if (inp && inp.value) {
        return inp.value;
      }
    }
    try {
      const fromUrl =
        new URL(window.location.href).searchParams.get("semester") || "";
      if (fromUrl) {
        return fromUrl;
      }
    } catch {
      /* ignore */
    }
    const root = document.getElementById("schedule-builder-grid-root");
    if (root) {
      const grid = root.querySelector(
        ".schedule-builder__grid[data-builder-active-semester]",
      );
      if (grid) {
        const ds = grid.getAttribute("data-builder-active-semester");
        if (ds) {
          return ds;
        }
      }
    }
    return "";
  }

  function builderReturnPath() {
    return window.location.pathname + window.location.search;
  }

  global.TcfSchedulePage = {
    activeSemesterId,
    builderReturnPath,
  };
})(window);
