/**
 * Fetch sorted review markup and swap #reviews-results without a full reload.
 */
(function (global) {
  /**
   * @param {{
   *   sortSelectId: string,
   *   resultsId: string,
   *   hash?: string,
   * }} opts
   */
  function init(opts) {
    const sortSelect = document.getElementById(opts.sortSelectId);
    const reviewsResults = document.getElementById(opts.resultsId);
    if (!sortSelect || !reviewsResults) {
      return;
    }
    const hash = opts.hash || "reviews";

    function syncLastSortFromDom() {
      sortSelect.dataset.lastSort =
        sortSelect.value ||
        new URL(window.location.href).searchParams.get("sort") ||
        "";
    }
    syncLastSortFromDom();

    sortSelect.addEventListener("change", async function (e) {
      const selectedMethod = e.target.value;
      const previousSort = sortSelect.dataset.lastSort || "";

      const url = new URL(window.location.href);
      url.searchParams.delete("page");
      if (selectedMethod) {
        url.searchParams.set("sort", selectedMethod);
      } else {
        url.searchParams.delete("sort");
      }
      url.hash = hash;

      sortSelect.disabled = true;
      try {
        const fetchUrl = url.pathname + url.search;
        let res;
        if (global.TcfHttp && global.TcfHttp.fetchHtml) {
          res = await global.TcfHttp.fetchHtml(fetchUrl);
        } else {
          res = await fetch(fetchUrl, {
            credentials: "same-origin",
            headers: { "X-Requested-With": "XMLHttpRequest" },
          });
        }
        if (!res.ok) {
          throw new Error("Failed to load sorted reviews.");
        }
        const html = await res.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");
        const nextResults = doc.getElementById(opts.resultsId);
        if (!nextResults) {
          throw new Error("Missing reviews content.");
        }
        reviewsResults.innerHTML = nextResults.innerHTML;
        sortSelect.dataset.lastSort = selectedMethod;
        history.replaceState({}, "", url.pathname + url.search + "#" + hash);
        if (
          global.reviewVotes &&
          typeof global.reviewVotes.init === "function"
        ) {
          global.reviewVotes.init();
        }
      } catch {
        sortSelect.value = previousSort;
        const anchor =
          sortSelect.closest(".reviews-header__actions") ||
          sortSelect.parentElement;
        const errorMsg = document.createElement("p");
        errorMsg.textContent = "Failed to load reviews. Please try again.";
        errorMsg.className = "text-danger text-sm mt-2";
        if (anchor) {
          anchor.appendChild(errorMsg);
        }
        setTimeout(function () {
          errorMsg.remove();
        }, 4000);
      } finally {
        sortSelect.disabled = false;
      }
    });
  }

  global.TcfReviewsSortFetch = { init };
})(window);
