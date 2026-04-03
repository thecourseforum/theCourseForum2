/**
 * Refresh the schedule builder grid via partial=grid.
 */
(function (global) {
  function historyUrlWithoutPartial(urlStr) {
    var u = new URL(urlStr, window.location.origin);
    u.searchParams.delete("partial");
    var q = u.searchParams.toString();
    return q ? u.pathname + "?" + q : u.pathname;
  }

  function syncSemesterFormHiddenFromUrl(urlStr) {
    var u = new URL(urlStr, window.location.origin);
    var form = document.querySelector(".schedule-builder__semester-form");
    if (!form) {
      return;
    }
    function setOrRemoveHidden(name, value) {
      var sel = 'input[type="hidden"][name="' + name + '"]';
      var inputs = form.querySelectorAll(sel);
      if (value === null || value === "") {
        inputs.forEach(function (inp) {
          inp.remove();
        });
        return;
      }
      var first = inputs[0];
      if (first) {
        first.value = value;
        for (var i = 1; i < inputs.length; i++) {
          inputs[i].remove();
        }
      } else {
        var h = document.createElement("input");
        h.type = "hidden";
        h.name = name;
        h.value = value;
        form.appendChild(h);
      }
    }
    var sch = u.searchParams.get("schedule");
    var cmp = u.searchParams.get("compare");
    var ov = u.searchParams.get("overlap");
    if (sch) {
      setOrRemoveHidden("schedule", sch);
    } else {
      setOrRemoveHidden("schedule", null);
    }
    setOrRemoveHidden("compare", cmp || null);
    setOrRemoveHidden("overlap", ov || null);
  }

  /**
   * @param {string} fetchUrl
   * @param {string} [historyUrl]
   * @returns {Promise<void>}
   */
  function replaceGridFromUrl(fetchUrl, historyUrl) {
    var root = document.getElementById("schedule-builder-grid-root");
    if (!root || !global.TcfPartialHtml) {
      return Promise.resolve();
    }
    var u = new URL(fetchUrl, window.location.origin);
    u.searchParams.set("partial", "grid");
    root.setAttribute("aria-busy", "true");
    var hist = historyUrl || fetchUrl;
    return global.TcfPartialHtml.fetchHtml(u.toString())
      .then(function (res) {
        if (!res.ok) {
          window.location.assign(historyUrlWithoutPartial(hist));
          return;
        }
        return res.text();
      })
      .then(function (html) {
        if (html == null) {
          return;
        }
        global.TcfPartialHtml.replaceInner(root, html);
        var cleanHist = historyUrlWithoutPartial(hist);
        history.replaceState(null, "", cleanHist);
        syncSemesterFormHiddenFromUrl(cleanHist);
        if (typeof global.initSearchBarContainersIn === "function") {
          global.initSearchBarContainersIn(root);
        }
      })
      .finally(function () {
        root.removeAttribute("aria-busy");
      });
  }

  global.TcfScheduleGrid = {
    replaceFromUrl: replaceGridFromUrl,
    historyUrlWithoutPartial: historyUrlWithoutPartial,
  };
})(window);
