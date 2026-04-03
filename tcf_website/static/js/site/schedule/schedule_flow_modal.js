/**
 * Modal flows for new schedule and add-to-schedule (JSON POST + optional grid refresh).
 */
(function () {
  const MODAL_ID = "scheduleFlowModal";
  const BODY_ID = "scheduleFlowModalBody";
  const TITLE_ID = "scheduleFlowModalTitle";

  function getModalBody() {
    return document.getElementById(BODY_ID);
  }

  function setTitle(text) {
    const el = document.getElementById(TITLE_ID);
    if (el) {
      el.textContent = text || "Schedule";
    }
  }

  function setBodyHtml(html) {
    const el = getModalBody();
    if (el) {
      el.innerHTML = html;
    }
  }

  function clearFormError(form) {
    const err = form.querySelector("[data-tcf-form-error]");
    if (err) {
      err.textContent = "";
      err.hidden = true;
    }
  }

  function showFormError(form, message) {
    const err = form.querySelector("[data-tcf-form-error]");
    if (err) {
      err.textContent = message;
      err.hidden = false;
    }
  }

  function getCookie(name) {
    if (window.TcfHttp && window.TcfHttp.getCookie) {
      return window.TcfHttp.getCookie(name);
    }
    const m = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
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
    const root = document.getElementById("schedule-builder-grid-root");
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
      const action = form.getAttribute("action");
      if (!action) {
        return;
      }
      const fd = new FormData(form);
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
          const ct = res.headers.get("content-type") || "";
          if (ct.indexOf("application/json") === -1) {
            return res.text().then(function () {
              return {
                res,
                data: { ok: false, error: "Unexpected response." },
              };
            });
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
          if (out.res.ok && out.data && out.data.ok && out.data.redirect) {
            afterScheduleSuccess(out.data.redirect);
            return;
          }
          const msg =
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

  function ensureHiddenInput(form, name, value) {
    let el = form.querySelector('input[type="hidden"][name="' + name + '"]');
    if (!el) {
      el = document.createElement("input");
      el.type = "hidden";
      el.name = name;
      const csrf = form.querySelector('input[name="csrfmiddlewaretoken"]');
      if (csrf && csrf.nextSibling) {
        form.insertBefore(el, csrf.nextSibling);
      } else {
        form.appendChild(el);
      }
    }
    el.value = value;
  }

  /**
   * New-schedule modal is cloned from a <template> rendered once on load; hidden
   * semester/next must match live builder state (term combo + location).
   */
  function syncNewScheduleFormFromBuilder(form) {
    if (!form) {
      return;
    }
    const page = window.TcfSchedulePage;
    const nextPath =
      page && page.builderReturnPath
        ? page.builderReturnPath()
        : window.location.pathname + window.location.search;
    const sem =
      page && page.activeSemesterId ? page.activeSemesterId() || "" : "";
    ensureHiddenInput(form, "next", nextPath);
    if (sem) {
      ensureHiddenInput(form, "semester", sem);
    }
  }

  function openNewScheduleFromTemplate() {
    const tpl = document.getElementById("tcf-new-schedule-form-template");
    if (!tpl || !window.modal) {
      return;
    }
    setTitle("New schedule");
    setBodyHtml(tpl.innerHTML);
    openModal();
    const body = getModalBody();
    if (body) {
      const f = body.querySelector("form[data-tcf-json-submit]");
      syncNewScheduleFormFromBuilder(f);
      wireJsonForm(f);
    }
  }

  function fetchAddCourseModal(url) {
    if (!window.TcfPartialHtml || !window.modal) {
      window.location.assign(url);
      return;
    }
    const u = new URL(url, window.location.origin);
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
        const body = getModalBody();
        if (body) {
          const f = body.querySelector("form[data-tcf-json-submit]");
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
      const t = ev.target;
      if (!(t instanceof Element)) {
        return;
      }
      const newBtn = t.closest("[data-schedule-flow-new]");
      if (newBtn) {
        ev.preventDefault();
        openNewScheduleFromTemplate();
        return;
      }
      const addTrigger = t.closest("[data-schedule-flow-add-url]");
      if (addTrigger) {
        ev.preventDefault();
        const addUrl = addTrigger.getAttribute("data-schedule-flow-add-url");
        if (addUrl) {
          fetchAddCourseModal(addUrl);
        }
      }
    },
    true,
  );
})();
