/** Progressive enhancement: ordinary GET forms and detail links work without JS. */
(function () {
  "use strict";

  const form = document.getElementById("eventFilters");
  const results = document.getElementById("eventResults");
  if (!form || !results || !window.TcfPartialHtml || !window.modal) return;

  const status = document.getElementById("eventLoadStatus");
  const error = document.getElementById("eventLoadError");
  const dialog = document.getElementById("clubEventModal");
  const content = document.getElementById("clubEventContent");
  let listController;
  let detailController;
  let pendingUrl;

  const filters = document.querySelector(".event-filters");
  const mobile = window.matchMedia("(max-width: 767px)");
  filters.open =
    !mobile.matches || Boolean(results.querySelector('[role="alert"]'));
  mobile.addEventListener("change", () => {
    filters.open = !mobile.matches;
  });

  /**
   * Load filtered results, cancel superseded requests, and update browser history.
   * Keep prior results on failure and retain the submitted URL for retry.
   * @param {string} url - List URL with filters and an optional results anchor.
   * @returns {Promise<void>} Resolves after rendering results or recovery feedback.
   */
  async function updateList(url) {
    listController?.abort();
    const controller = new AbortController();
    listController = controller;
    pendingUrl = url;
    error.hidden = true;
    status.classList.remove("sr-only");
    status.textContent = "Loading events…";
    results.setAttribute("aria-busy", "true");
    const requestUrl = new URL(url);
    requestUrl.searchParams.set("partial", "results");
    const timeout = setTimeout(() => controller.abort("timeout"), 20000);
    try {
      const response = await window.TcfPartialHtml.fetchHtml(requestUrl.href, {
        signal: controller.signal,
      });
      if (!response.ok) throw new Error("Event request failed");
      const html = await response.text();
      if (controller.signal.aborted) return;
      window.TcfPartialHtml.replaceInner(results, html);
      const cleanUrl = new URL(url);
      cleanUrl.searchParams.delete("partial");
      cleanUrl.hash = "";
      if (cleanUrl.href !== window.location.href)
        history.pushState(null, "", cleanUrl.href);
      status.textContent =
        results
          .querySelector(".event-results-count")
          ?.textContent.replace(/\s+/g, " ")
          .trim() || "Check your event filters.";
      status.classList.add("sr-only");
      results.focus({ preventScroll: true });
      if (new URL(url).hash === "#eventResults") {
        results.scrollIntoView({ block: "start" });
      }
    } catch (failure) {
      if (controller.signal.aborted && controller.signal.reason !== "timeout")
        return;
      error.hidden = false;
      status.textContent = "";
    } finally {
      clearTimeout(timeout);
      if (listController === controller) results.removeAttribute("aria-busy");
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const url = new URL(form.action);
    url.search = new URLSearchParams(new FormData(form)).toString();
    updateList(url.href);
  });

  document
    .getElementById("eventRetry")
    .addEventListener("click", () => updateList(pendingUrl));
  // Reload the server-rendered form as well as the results when restoring history.
  window.addEventListener("popstate", () => window.location.reload());

  /**
   * Load the selected event into the modal, canceling any previous detail request.
   * Offer retry and the normal event page when the request fails or times out.
   * @param {string} href - Event detail URL, also used for the fallback link.
   * @returns {Promise<void>} Resolves after rendering details or recovery feedback.
   */
  async function loadDetails(href) {
    detailController?.abort();
    const controller = new AbortController();
    detailController = controller;
    content.innerHTML =
      '<h2 id="clubEventTitle">Event details</h2><p role="status">Loading event…</p>';
    const url = new URL(href);
    url.searchParams.set("partial", "details");
    const timeout = setTimeout(() => controller.abort("timeout"), 20000);
    try {
      const response = await window.TcfPartialHtml.fetchHtml(url.href, {
        signal: controller.signal,
      });
      if (!response.ok) throw new Error("Event details unavailable");
      const html = await response.text();
      if (!controller.signal.aborted)
        window.TcfPartialHtml.replaceInner(content, html);
    } catch (failure) {
      if (controller.signal.aborted && controller.signal.reason !== "timeout")
        return;
      content.innerHTML =
        '<h2 id="clubEventTitle">Event details unavailable</h2><p role="alert">We couldn’t load this event. Try again or open its page.</p>';
      const retry = document.createElement("button");
      retry.type = "button";
      retry.className = "btn btn--secondary btn--md";
      retry.textContent = "Try again";
      retry.addEventListener("click", () => loadDetails(href));
      const fallback = document.createElement("a");
      fallback.href = href;
      fallback.className = "btn btn--secondary btn--md";
      fallback.textContent = "Open event page";
      content.append(retry, " ", fallback);
    } finally {
      clearTimeout(timeout);
    }
  }

  dialog.addEventListener("modal:close", () => detailController?.abort());
  results.addEventListener("click", (event) => {
    if (
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    )
      return;
    const link = event.target.closest("a");
    if (!link) return;
    if (link.hasAttribute("data-event-detail")) {
      event.preventDefault();
      link.focus();
      loadDetails(link.href);
      window.modal.open("clubEventModal");
    } else if (link.closest(".pagination")) {
      event.preventDefault();
      updateList(link.href);
    }
  });
})();
