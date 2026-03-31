// Shared utility: add Up/Down arrow key navigation between an input and a
// container of focusable items. Used by both the search bar autocomplete and
// the combo-box dropdowns on the browse page.
function addArrowKeyNav(input, container, itemSelector) {
  function getItems() {
    return Array.from(container.querySelectorAll(itemSelector));
  }
  function isOpen() {
    return !container.hidden && container.style.display !== "none";
  }
  input.addEventListener("keydown", (e) => {
    if (!isOpen()) return;
    const items = getItems();
    if (!items.length) return;
    const activeIdx = items.findIndex((item) => document.activeElement === item);
    if (e.key === "ArrowDown") {
      e.preventDefault();
      items[activeIdx < items.length - 1 ? activeIdx + 1 : 0].focus();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      items[activeIdx > 0 ? activeIdx - 1 : items.length - 1].focus();
    }
  });
  container.addEventListener("keydown", (e) => {
    const items = getItems();
    const activeIdx = items.findIndex((item) => document.activeElement === item);
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (activeIdx < items.length - 1) items[activeIdx + 1].focus();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (activeIdx > 0) items[activeIdx - 1].focus();
      else input.focus();
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".search-bar-container").forEach((container) => {
    const form = container.querySelector("form");
    const searchInput = container.querySelector(".search-bar__input");
    const autocompleteContainer = container.querySelector(
      ".autocomplete-dropdown-container",
    );

    let autocompleteTimeout = null;

    if (searchInput && autocompleteContainer) {
      if (autocompleteContainer.getAttribute("data-autocomplete-action")) {
        form.addEventListener("submit", (e) => {
          e.preventDefault();
          const firstLink = autocompleteContainer.querySelector(
            ".autocomplete-item__link",
          );
          if (firstLink) {
            firstLink.click();
          }
        });
      }
      searchInput.addEventListener("input", (e) => {
        const query = e.target.value.trim();
        const mode =
          form.querySelector('input[name="mode"]')?.value || "courses";

        if (query.length < 2) {
          autocompleteContainer.style.display = "none";
          autocompleteContainer.innerHTML = "";
          return;
        }

        clearTimeout(autocompleteTimeout);
        autocompleteTimeout = setTimeout(() => {
          const url = new URL(form.action, window.location.origin);
          url.searchParams.set("q", query);
          url.searchParams.set("mode", mode);

          const action = autocompleteContainer.getAttribute(
            "data-autocomplete-action",
          );
          const target = autocompleteContainer.getAttribute(
            "data-autocomplete-target",
          );
          if (action) url.searchParams.set("autocomplete_action", action);
          if (target) url.searchParams.set("autocomplete_target", target);

          fetch(url, {
            headers: {
              "X-Requested-With": "XMLHttpRequest",
            },
          })
            .then((res) => res.text())
            .then((html) => {
              autocompleteContainer.innerHTML = html;
              autocompleteContainer.style.display = "block";
            })
            .catch((err) => {
              console.error("Autocomplete error:", err);
            });
        }, 200);
      });

      // Hide autocomplete on click outside
      document.addEventListener("click", (e) => {
        if (
          !autocompleteContainer.contains(e.target) &&
          e.target !== searchInput
        ) {
          autocompleteContainer.style.display = "none";
        }
      });

      // Select option on enter, or show autocomplete again on focus
      searchInput.addEventListener("focus", () => {
        if (
          searchInput.value.trim().length >= 2 &&
          autocompleteContainer.innerHTML.trim() !== ""
        ) {
          autocompleteContainer.style.display = "block";
        }
      });

      addArrowKeyNav(
        searchInput,
        autocompleteContainer,
        ".autocomplete-item__link, .autocomplete-item__title",
      );
    }
  });
});
