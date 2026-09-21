/**
 * Quick Rate
 * ==========
 * Each .quick-rate-row is its own form. Submitting posts one review and
 * collapses the row; "Didn't take it" records a dismissal and removes it.
 */

(function () {
  "use strict";

  const root = document.querySelector(".quick-rate");
  if (!root) {
    return;
  }

  const { submitUrl, dismissUrl, instructorsUrl } = root.dataset;
  const countEl = document.getElementById("quick-rate-count");
  const MIN_TEXT = 200;

  async function post(url, formData) {
    const response = await fetch(url, {
      method: "POST",
      body: formData,
      credentials: "same-origin",
      headers: {
        "X-CSRFToken": formData.get("csrfmiddlewaretoken"),
        "X-Requested-With": "XMLHttpRequest",
      },
    });
    let payload = {};
    try {
      payload = await response.json();
    } catch {
      payload = {};
    }
    return { response, payload };
  }

  function showError(row, message) {
    const el = row.querySelector("[data-quick-rate-error]");
    el.textContent = message;
    el.hidden = false;
  }

  function firstErrorMessage(errors) {
    const lists = Object.values(errors || {});
    if (lists.length && lists[0].length && lists[0][0].message) {
      return lists[0][0].message;
    }
    return "Could not save this rating. Check the fields and try again.";
  }

  function collapse(row, message) {
    const title = row.querySelector(".quick-rate-row__code").textContent;
    const done = document.createElement("div");
    done.className = "quick-rate-row quick-rate-row--done";
    done.textContent = `${title}: ${message}`;
    row.replaceWith(done);
  }

  async function submitRow(row) {
    const button = row.querySelector('button[type="submit"]');
    button.disabled = true;
    try {
      const { response, payload } = await post(submitUrl, new FormData(row));
      if (response.ok && payload.ok) {
        collapse(row, "rated. Thank you!");
        if (countEl) {
          countEl.textContent = String(Number(countEl.textContent) + 1);
        }
        document.dispatchEvent(
          new CustomEvent("tcf:quick-rate-saved", { detail: payload }),
        );
        return;
      }
      if (response.status === 409) {
        collapse(row, "you already reviewed this one.");
        return;
      }
      showError(row, firstErrorMessage(payload.errors));
    } catch {
      showError(row, "Network error. Please try again.");
    }
    button.disabled = false;
  }

  async function dismissRow(row) {
    const formData = new FormData(row);
    try {
      const { response } = await post(dismissUrl, formData);
      if (response.ok) {
        row.remove();
        return;
      }
    } catch {
      // fall through to the message below
    }
    showError(row, "Could not remove this course. Please try again.");
  }

  async function loadInstructors(row, semesterId) {
    const select = row.querySelector("[data-quick-rate-instructor]");
    select.disabled = true;
    select.replaceChildren(new Option("Loading…", ""));
    if (!semesterId) {
      select.replaceChildren(new Option("Choose a semester first", ""));
      return;
    }
    const courseId = row.querySelector('input[name="course"]').value;
    const url = new URL(instructorsUrl, window.location.origin);
    url.searchParams.set("course", courseId);
    url.searchParams.set("semester", semesterId);
    try {
      const response = await fetch(url, { credentials: "same-origin" });
      const data = await response.json();
      const options = [new Option("Choose…", "")];
      (data.instructors || []).forEach((i) => {
        options.push(new Option(`${i.first_name} ${i.last_name}`.trim(), i.id));
      });
      select.replaceChildren(...options);
      select.disabled = false;
    } catch {
      select.replaceChildren(new Option("Could not load instructors", ""));
    }
  }

  root.querySelectorAll("[data-quick-rate-row]").forEach((row) => {
    row.addEventListener("submit", (event) => {
      event.preventDefault();
      submitRow(row);
    });

    const dismiss = row.querySelector("[data-quick-rate-dismiss]");
    if (dismiss) {
      dismiss.addEventListener("click", () => dismissRow(row));
    }

    const semester = row.querySelector("[data-quick-rate-semester]");
    if (semester) {
      semester.addEventListener("change", () =>
        loadInstructors(row, semester.value),
      );
    }

    const text = row.querySelector("[data-quick-rate-text]");
    const counter = row.querySelector("[data-quick-rate-charcount]");
    if (text && counter) {
      text.addEventListener("input", () => {
        const length = text.value.trim().length;
        if (length === 0) {
          counter.textContent = "Optional";
        } else if (length < MIN_TEXT) {
          counter.textContent = `${length}/${MIN_TEXT} characters`;
        } else {
          counter.textContent = `${length} characters`;
        }
      });
    }
  });
})();
