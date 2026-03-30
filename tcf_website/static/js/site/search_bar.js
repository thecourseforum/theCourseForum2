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

      // Handle keyboard navigation simple way: Up/Down
      searchInput.addEventListener("keydown", (e) => {
        if (autocompleteContainer.style.display !== "block") return;
        const items = Array.from(
          autocompleteContainer.querySelectorAll(
            ".autocomplete-item__link, .autocomplete-item__title",
          ),
        ); // if no link, select title
        if (!items.length) return;

        const activeIdx = items.findIndex(
          (item) => document.activeElement === item,
        );

        if (e.key === "ArrowDown") {
          e.preventDefault();
          if (activeIdx < items.length - 1) items[activeIdx + 1].focus();
          else items[0].focus();
        } else if (e.key === "ArrowUp") {
          e.preventDefault();
          if (activeIdx > 0) items[activeIdx - 1].focus();
          else items[items.length - 1].focus();
        } else if (
          document.activeElement !== searchInput &&
          e.key === "Enter"
        ) {
          // Allow natural link following
        }
      });

      autocompleteContainer.addEventListener("keydown", (e) => {
        // Similar handling inside container
        const items = Array.from(
          autocompleteContainer.querySelectorAll(".autocomplete-item__link"),
        );
        const activeIdx = items.findIndex(
          (item) => document.activeElement === item,
        );
        if (e.key === "ArrowDown") {
          e.preventDefault();
          if (activeIdx < items.length - 1) items[activeIdx + 1].focus();
        } else if (e.key === "ArrowUp") {
          e.preventDefault();
          if (activeIdx > 0) items[activeIdx - 1].focus();
          else searchInput.focus();
        }
      });
    }
  });
});
