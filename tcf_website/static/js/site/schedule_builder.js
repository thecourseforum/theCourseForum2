/**
 * Schedule builder: partial=grid navigation, compare pick modal, term change via partial (no full reload).
 */
(function () {
  const root = document.getElementById("schedule-builder-grid-root");
  if (!root || !window.TcfScheduleGrid) {
    return;
  }

  const BUILDER_QUERY_KEYS = ["semester", "schedule", "compare", "overlap"];

  function scheduleBuilderBaseUrl() {
    return root.dataset.scheduleBaseUrl || "/schedule/";
  }

  /**
   * Current builder query (semester / schedule / compare / overlap) from form + URL fallback.
   */
  function scheduleBuilderQueryUrl() {
    const u = new URL(scheduleBuilderBaseUrl(), window.location.origin);
    const form = document.querySelector(".schedule-builder__semester-form");
    const cur = new URL(window.location.href);
    const keys = ["semester", "schedule", "compare", "overlap"];
    keys.forEach(function (k) {
      let v = null;
      if (form) {
        const inp = form.querySelector('input[name="' + k + '"]');
        if (inp && inp.value) {
          v = inp.value;
        }
      }
      if (!v && cur.searchParams.get(k)) {
        v = cur.searchParams.get(k);
      }
      if (v) {
        u.searchParams.set(k, v);
      }
    });
    return u;
  }

  function fetchAndReplaceGrid(fetchUrl, historyUrl) {
    window.TcfScheduleGrid.replaceFromUrl(fetchUrl, historyUrl);
  }

  function csrfTokenFromCookie() {
    if (window.TcfHttp && window.TcfHttp.getCookie) {
      return window.TcfHttp.getCookie("csrftoken");
    }
    const m = document.cookie.match(/(^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[2]) : "";
  }

  document.addEventListener(
    "submit",
    function (ev) {
      const form = ev.target;
      if (!(form instanceof HTMLFormElement)) {
        return;
      }
      if (form.classList.contains("schedule-builder__semester-form")) {
        ev.preventDefault();
        const fd = new FormData(form);
        const actionAttr = form.getAttribute("action");
        const u = new URL(
          actionAttr || scheduleBuilderBaseUrl(),
          window.location.origin,
        );
        BUILDER_QUERY_KEYS.forEach(function (key) {
          const v = fd.get(key);
          if (v != null && String(v) !== "") {
            u.searchParams.set(key, String(v));
          }
        });
        fetchAndReplaceGrid(u.toString(), u.toString());
        return;
      }
      if (!root.contains(form) || !form.hasAttribute("data-schedule-async")) {
        return;
      }
      ev.preventDefault();
      const postAction = form.getAttribute("action");
      if (!postAction) {
        return;
      }
      const token = csrfTokenFromCookie();
      const asyncHeaders = {
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
      };
      if (token) {
        asyncHeaders["X-CSRFToken"] = token;
      }
      /* form.action is wrong when the form has <input name="action"> (e.g. share enable/disable). */
      fetch(postAction, {
        method: "POST",
        body: new FormData(form),
        credentials: "same-origin",
        headers: asyncHeaders,
      })
        .then(function (res) {
          const ct = res.headers.get("content-type") || "";
          if (ct.indexOf("application/json") === -1) {
            throw new Error("non-json");
          }
          return res.json().then(function (data) {
            return { res, data };
          });
        })
        .then(function (out) {
          if (
            window.TcfFlashMessages &&
            out.data &&
            out.data.messages &&
            out.data.messages.length
          ) {
            window.TcfFlashMessages.showFromJson(out.data.messages);
          }
          if (out.res.ok && out.data.ok && out.data.redirect) {
            fetchAndReplaceGrid(out.data.redirect, out.data.redirect);
            return;
          }
          const msg =
            (out.data && out.data.error) || "Something went wrong. Try again.";
          if (!out.data || !out.data.messages || !out.data.messages.length) {
            window.alert(msg);
          }
        })
        .catch(function () {
          window.location.reload();
        });
    },
    true,
  );

  document.addEventListener(
    "click",
    function (ev) {
      const t = ev.target;
      if (!(t instanceof Element)) {
        return;
      }

      const openPick = t.closest("[data-schedule-open-compare-pick]");
      if (openPick && root.contains(openPick)) {
        ev.preventDefault();
        const pickUrl = scheduleBuilderQueryUrl();
        pickUrl.searchParams.delete("partial");
        pickUrl.searchParams.delete("compare");
        pickUrl.searchParams.delete("overlap");
        pickUrl.searchParams.set("partial", "compare_pick");
        const bodyEl = document.getElementById("scheduleComparePickModalBody");
        if (!bodyEl || !window.TcfPartialHtml || !window.modal) {
          return;
        }
        bodyEl.innerHTML = '<p class="text-muted text-sm">Loading…</p>';
        window.TcfPartialHtml.fetchHtml(pickUrl.toString())
          .then(function (res) {
            if (!res.ok) {
              throw new Error("bad status");
            }
            return res.text();
          })
          .then(function (html) {
            window.TcfPartialHtml.replaceInner(bodyEl, html);
            window.modal.open("scheduleComparePickModal");
          })
          .catch(function () {
            window.TcfPartialHtml.replaceInner(
              bodyEl,
              '<p class="text-muted text-sm">Could not load schedules. Try again.</p>',
            );
            window.modal.open("scheduleComparePickModal");
          });
        return;
      }

      const apply = t.closest("[data-schedule-apply-compare]");
      if (apply) {
        ev.preventDefault();
        const compareId = apply.getAttribute("data-schedule-apply-compare");
        if (!compareId) {
          return;
        }
        const u = scheduleBuilderQueryUrl();
        u.searchParams.delete("partial");
        const primary = u.searchParams.get("schedule");
        if (!primary) {
          return;
        }
        u.searchParams.set("compare", compareId);
        u.searchParams.delete("overlap");
        fetchAndReplaceGrid(u.toString(), u.toString());
        if (window.modal) {
          window.modal.close();
        }
        return;
      }

      const a = t.closest("a[data-schedule-nav]");
      if (a && root.contains(a)) {
        ev.preventDefault();
        ev.stopPropagation();
        fetchAndReplaceGrid(a.href, a.href);
      }
    },
    true,
  );

  root.addEventListener("click", function (ev) {
    const copyBtn = ev.target.closest(".schedule-detail__share-copy");
    if (!copyBtn || !root.contains(copyBtn)) {
      return;
    }
    const sroot = copyBtn.closest("[data-schedule-share]");
    if (!sroot) {
      return;
    }
    const input = sroot.querySelector(".schedule-detail__share-input");
    if (!input) {
      return;
    }
    const v = input.value;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(v).catch(function () {
        input.select();
        document.execCommand("copy");
      });
    } else {
      input.select();
      document.execCommand("copy");
    }
  });
})();
