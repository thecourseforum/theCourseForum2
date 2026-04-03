/**
 * Schedule builder: partial=grid navigation, compare pick modal, semester combo without full reload.
 */
(function () {
  var root = document.getElementById("schedule-builder-grid-root");
  if (!root || !window.TcfScheduleGrid) {
    return;
  }

  function scheduleBuilderBaseUrl() {
    return root.dataset.scheduleBaseUrl || "/schedule/";
  }

  /**
   * Current builder query (semester / schedule / compare / overlap) from form + URL fallback.
   */
  function scheduleBuilderQueryUrl() {
    var u = new URL(scheduleBuilderBaseUrl(), window.location.origin);
    var form = document.querySelector(".schedule-builder__semester-form");
    var cur = new URL(window.location.href);
    var keys = ["semester", "schedule", "compare", "overlap"];
    keys.forEach(function (k) {
      var v = null;
      if (form) {
        var inp = form.querySelector('input[name="' + k + '"]');
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
    var m = document.cookie.match(/(^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[2]) : "";
  }

  document.addEventListener(
    "submit",
    function (ev) {
      var form = ev.target;
      if (!(form instanceof HTMLFormElement)) {
        return;
      }
      if (form.classList.contains("schedule-builder__semester-form")) {
        ev.preventDefault();
        var fd = new FormData(form);
        var u = new URL(scheduleBuilderBaseUrl(), window.location.origin);
        var semester = fd.get("semester");
        if (semester) {
          u.searchParams.set("semester", semester);
        }
        fetchAndReplaceGrid(u.toString(), u.toString());
        return;
      }
      if (!root.contains(form) || !form.hasAttribute("data-schedule-async")) {
        return;
      }
      ev.preventDefault();
      var postAction = form.getAttribute("action");
      if (!postAction) {
        return;
      }
      var token = csrfTokenFromCookie();
      var asyncHeaders = {
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
          var ct = res.headers.get("content-type") || "";
          if (ct.indexOf("application/json") === -1) {
            throw new Error("non-json");
          }
          return res.json().then(function (data) {
            return { res: res, data: data };
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
          var msg =
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
      var t = ev.target;
      if (!(t instanceof Element)) {
        return;
      }

      var openPick = t.closest("[data-schedule-open-compare-pick]");
      if (openPick && root.contains(openPick)) {
        ev.preventDefault();
        var pickUrl = scheduleBuilderQueryUrl();
        pickUrl.searchParams.delete("partial");
        pickUrl.searchParams.delete("compare");
        pickUrl.searchParams.delete("overlap");
        pickUrl.searchParams.set("partial", "compare_pick");
        var bodyEl = document.getElementById("scheduleComparePickModalBody");
        if (!bodyEl || !window.TcfPartialHtml || !window.modal) {
          return;
        }
        bodyEl.innerHTML =
          '<p class="text-muted text-sm">Loading…</p>';
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

      var apply = t.closest("[data-schedule-apply-compare]");
      if (apply) {
        ev.preventDefault();
        var compareId = apply.getAttribute("data-schedule-apply-compare");
        if (!compareId) {
          return;
        }
        var u = scheduleBuilderQueryUrl();
        u.searchParams.delete("partial");
        var primary = u.searchParams.get("schedule");
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

      var a = t.closest("a[data-schedule-nav]");
      if (a && root.contains(a)) {
        ev.preventDefault();
        ev.stopPropagation();
        fetchAndReplaceGrid(a.href, a.href);
      }
    },
    true,
  );

  root.addEventListener("click", function (ev) {
    var copyBtn = ev.target.closest(".schedule-detail__share-copy");
    if (!copyBtn || !root.contains(copyBtn)) {
      return;
    }
    var sroot = copyBtn.closest("[data-schedule-share]");
    if (!sroot) {
      return;
    }
    var input = sroot.querySelector(".schedule-detail__share-input");
    if (!input) {
      return;
    }
    var v = input.value;
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
