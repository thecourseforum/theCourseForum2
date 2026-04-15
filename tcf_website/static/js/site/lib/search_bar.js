// Shared utility: add Up/Down arrow key navigation between an input and a
// container of focusable items. Used by the search bar autocomplete and
// combo_dropdown.js (searchable selects).
function addArrowKeyNav(
  input,
  container,
  itemSelector,
  { upLoops = true, downLoops = true } = {},
) {
  function getItems() {
    return Array.from(container.querySelectorAll(itemSelector));
  }
  function isOpen() {
    return !container.hidden;
  }
  input.addEventListener("keydown", (e) => {
    if (!isOpen()) return;
    const items = getItems();
    if (!items.length) return;
    const activeIdx = items.findIndex(
      (item) => document.activeElement === item,
    );
    if (e.key === "ArrowDown") {
      e.preventDefault();
      const next =
        activeIdx < items.length - 1 ? activeIdx + 1 : downLoops ? 0 : -1;
      if (next >= 0) items[next].focus();
    } else if (e.key === "ArrowUp" && upLoops) {
      e.preventDefault();
      items[activeIdx > 0 ? activeIdx - 1 : items.length - 1].focus();
    }
  });
  container.addEventListener("keydown", (e) => {
    const items = getItems();
    const activeIdx = items.findIndex(
      (item) => document.activeElement === item,
    );
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (activeIdx < items.length - 1) items[activeIdx + 1].focus();
      else if (downLoops) items[0].focus();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (activeIdx > 0) items[activeIdx - 1].focus();
      else if (upLoops) input.focus();
    }
  });
}

window.addArrowKeyNav = addArrowKeyNav;

(function () {
  let docCloseBound = false;

  function bindDocumentCloseOnce() {
    if (docCloseBound) {
      return;
    }
    docCloseBound = true;
    document.addEventListener("click", function (e) {
      const t = e.target;
      document
        .querySelectorAll(".search-bar-container")
        .forEach(function (ctr) {
          const ac = ctr.querySelector(".autocomplete-dropdown-container");
          const input = ctr.querySelector(".search-bar__input");
          if (!ac || !input) {
            return;
          }
          if (ac.contains(t) || t === input) {
            return;
          }
          ac.hidden = true;
        });
    });
  }

  function initSearchBarContainer(container) {
    if (container.getAttribute("data-search-bar-init") === "1") {
      return;
    }
    container.setAttribute("data-search-bar-init", "1");
    bindDocumentCloseOnce();

    const form = container.querySelector("form");
    const searchInput = container.querySelector(".search-bar__input");
    const autocompleteContainer = container.querySelector(
      ".autocomplete-dropdown-container",
    );
    if (!form || !searchInput || !autocompleteContainer) {
      return;
    }

    let autocompleteTimeout = null;

    if (autocompleteContainer.getAttribute("data-autocomplete-action")) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        const firstLink = autocompleteContainer.querySelector(
          ".autocomplete-item__link",
        );
        if (firstLink) {
          firstLink.click();
        }
      });
    }

    searchInput.addEventListener("input", function (e) {
      const query = e.target.value.trim();
      const modeInput = form.querySelector('input[name="mode"]');
      const mode = modeInput ? modeInput.value : "courses";

      if (query.length < 2) {
        autocompleteContainer.hidden = true;
        autocompleteContainer.innerHTML = "";
        return;
      }

      clearTimeout(autocompleteTimeout);
      autocompleteTimeout = setTimeout(function () {
        const url = new URL(form.action, window.location.origin);
        url.searchParams.set("q", query);
        url.searchParams.set("mode", mode);

        const action = autocompleteContainer.getAttribute(
          "data-autocomplete-action",
        );
        const target = autocompleteContainer.getAttribute(
          "data-autocomplete-target",
        );
        if (action) {
          url.searchParams.set("autocomplete_action", action);
        }
        if (target) {
          url.searchParams.set("autocomplete_target", target);
        }

        url.searchParams.set(
          "next",
          window.location.pathname + window.location.search,
        );

        fetch(url, {
          headers: {
            "X-Requested-With": "XMLHttpRequest",
          },
        })
          .then(function (res) {
            return res.text();
          })
          .then(function (html) {
            autocompleteContainer.innerHTML = html;
            autocompleteContainer.hidden = false;
          })
          .catch(function (err) {
            console.error("Autocomplete error:", err);
          });
      }, 200);
    });

    searchInput.addEventListener("focus", function () {
      if (
        searchInput.value.trim().length >= 2 &&
        autocompleteContainer.innerHTML.trim() !== ""
      ) {
        autocompleteContainer.hidden = false;
      }
    });

    addArrowKeyNav(
      searchInput,
      autocompleteContainer,
      ".autocomplete-item__link, .autocomplete-item__title",
    );
  }

  /**
   * Wire schedule/header search bars inside root (e.g. after schedule grid partial swap).
   * @param {ParentNode} [root] - default document
   */
  function initSearchBarContainersIn(root) {
    const scope = root || document;
    scope
      .querySelectorAll(".search-bar-container")
      .forEach(initSearchBarContainer);
  }

  window.initSearchBarContainersIn = initSearchBarContainersIn;

  document.addEventListener("DOMContentLoaded", function () {
    initSearchBarContainersIn(document);
  });
})();
