/**
 * Modal flows for new schedule and add-to-schedule (JSON POST + optional grid refresh).
 */
(function () {
  var MODAL_ID = "scheduleFlowModal";
  var BODY_ID = "scheduleFlowModalBody";
  var TITLE_ID = "scheduleFlowModalTitle";

  function getModalBody() {
    return document.getElementById(BODY_ID);
  }

  function setTitle(text) {
    var el = document.getElementById(TITLE_ID);
    if (el) {
      el.textContent = text || "Schedule";
    }
  }

  function setBodyHtml(html) {
    var el = getModalBody();
    if (el) {
      el.innerHTML = html;
    }
  }

  function clearFormError(form) {
    var err = form.querySelector("[data-tcf-form-error]");
    if (err) {
      err.textContent = "";
      err.hidden = true;
    }
  }

  function showFormError(form, message) {
    var err = form.querySelector("[data-tcf-form-error]");
    if (err) {
      err.textContent = message;
      err.hidden = false;
    }
  }

  function getCookie(name) {
    var m = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return m ? decodeURIComponent(m[2]) : "";
  }

  function openModal() {
    if (window.modal) {
      window.modal.open(MODAL_ID);
    }
  }

  function closeModal() {
    if (window.modal) {
      window.modal.close();
    }
  }

  function afterScheduleSuccess(redirect) {
    closeModal();
    var root = document.getElementById("schedule-builder-grid-root");
    if (root && window.TcfScheduleGrid) {
      window.TcfScheduleGrid.replaceFromUrl(redirect, redirect);
    } else {
      window.location.assign(redirect);
    }
  }

  function wireJsonForm(form) {
    if (!form || form.getAttribute("data-tcf-json-wired")) {
      return;
    }
    form.setAttribute("data-tcf-json-wired", "1");
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      clearFormError(form);
      var action = form.getAttribute("action");
      if (!action) {
        return;
      }
      var fd = new FormData(form);
      fetch(action, {
        method: "POST",
        body: fd,
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
          "X-Requested-With": "XMLHttpRequest",
        },
      })
        .then(function (res) {
          var ct = res.headers.get("content-type") || "";
          if (ct.indexOf("application/json") === -1) {
            return res.text().then(function () {
              return {
                res: res,
                data: { ok: false, error: "Unexpected response." },
              };
            });
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
          if (out.res.ok && out.data && out.data.ok && out.data.redirect) {
            afterScheduleSuccess(out.data.redirect);
            return;
          }
          var msg =
            (out.data && out.data.error) ||
            (out.res.ok ? "Something went wrong." : "Request failed.");
          if (out.data && out.data.messages && out.data.messages.length) {
            clearFormError(form);
          } else {
            showFormError(form, msg);
          }
        })
        .catch(function () {
          showFormError(form, "Network error.");
        });
    });
  }

  function openNewScheduleFromTemplate() {
    var tpl = document.getElementById("tcf-new-schedule-form-template");
    if (!tpl || !window.modal) {
      return;
    }
    setTitle("New schedule");
    setBodyHtml(tpl.innerHTML);
    openModal();
    var body = getModalBody();
    if (body) {
      var f = body.querySelector("form[data-tcf-json-submit]");
      wireJsonForm(f);
    }
  }

  function fetchAddCourseModal(url) {
    if (!window.TcfPartialHtml || !window.modal) {
      window.location.assign(url);
      return;
    }
    var u = new URL(url, window.location.origin);
    u.searchParams.set("partial", "modal");
    setTitle("Add to schedule");
    setBodyHtml('<p class="schedule-flow-modal__loading">Loading…</p>');
    openModal();
    window.TcfPartialHtml.fetchHtml(u.toString())
      .then(function (res) {
        if (!res.ok) {
          closeModal();
          window.location.assign(url);
          return;
        }
        return res.text();
      })
      .then(function (html) {
        if (html == null) {
          return;
        }
        setBodyHtml(html);
        var body = getModalBody();
        if (body) {
          var f = body.querySelector("form[data-tcf-json-submit]");
          wireJsonForm(f);
        }
      })
      .catch(function () {
        closeModal();
        window.location.assign(url);
      });
  }

  document.addEventListener(
    "click",
    function (ev) {
      var t = ev.target;
      if (!(t instanceof Element)) {
        return;
      }
      var newBtn = t.closest("[data-schedule-flow-new]");
      if (newBtn) {
        ev.preventDefault();
        openNewScheduleFromTemplate();
        return;
      }
      var addTrigger = t.closest("[data-schedule-flow-add-url]");
      if (addTrigger) {
        ev.preventDefault();
        var addUrl = addTrigger.getAttribute("data-schedule-flow-add-url");
        if (addUrl) {
          fetchAddCourseModal(addUrl);
        }
      }
    },
    true,
  );
})();
