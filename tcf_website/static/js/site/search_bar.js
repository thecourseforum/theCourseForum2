document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".search-bar-container").forEach((container) => {
    const toggle = container.querySelector(".search-bar__filter-trigger");
    const dropdown = container.querySelector(".search-filters");
    const form = container.querySelector("form");
    const gpaSlider = container.querySelector('input[name="min_gpa"]');
    const searchInput = container.querySelector(".search-bar__input");
    const autocompleteContainer = container.querySelector(
      ".autocomplete-dropdown-container",
    );

    let autocompleteTimeout = null;

    if (searchInput && autocompleteContainer) {
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

    const updateActiveState = () => {
      if (!toggle) {
        return;
      }

      let hasActiveFilters = false;

      container
        .querySelectorAll('input[type="checkbox"]')
        .forEach((checkbox) => {
          if (checkbox.checked) {
            hasActiveFilters = true;
          }
        });

      container.querySelectorAll('input[type="time"]').forEach((input) => {
        if (input.value) {
          hasActiveFilters = true;
        }
      });

      if (gpaSlider && parseFloat(gpaSlider.value) > 0) {
        hasActiveFilters = true;
      }

      toggle.classList.toggle("is-active-filter", hasActiveFilters);
    };

    if (toggle && dropdown) {
      toggle.addEventListener("click", (e) => {
        e.stopPropagation();

        document
          .querySelectorAll(".search-filters.is-open")
          .forEach((openDropdown) => {
            if (openDropdown !== dropdown) {
              openDropdown.classList.remove("is-open");
              const openTrigger = openDropdown
                .closest(".search-bar-container")
                ?.querySelector(".search-bar__filter-trigger");
              if (openTrigger) {
                openTrigger.classList.remove("is-active");
              }
            }
          });

        dropdown.classList.toggle("is-open");
        toggle.classList.toggle("is-active");
      });

      document.addEventListener("click", (e) => {
        if (
          dropdown.classList.contains("is-open") &&
          !dropdown.contains(e.target) &&
          !toggle.contains(e.target)
        ) {
          dropdown.classList.remove("is-open");
          toggle.classList.remove("is-active");
        }
      });
    }

    if (gpaSlider) {
      const valueDisplay =
        gpaSlider.parentElement.querySelector(".gpa-value-display");
      if (valueDisplay) {
        gpaSlider.addEventListener("input", () => {
          valueDisplay.textContent = parseFloat(gpaSlider.value).toFixed(1);
        });
      }
    }

    const searchInputs = container.querySelectorAll("[data-filter-list]");
    searchInputs.forEach((input) => {
      input.addEventListener("keyup", () => {
        const listContainer = input
          .closest(".filter-list-container")
          ?.querySelector(".filter-list");
        if (!listContainer) {
          return;
        }

        const filterText = input.value.toLowerCase();
        listContainer.querySelectorAll(".filter-item").forEach((item) => {
          item.style.display = item.textContent
            .toLowerCase()
            .includes(filterText)
            ? "flex"
            : "none";
        });
      });
    });

    const clearButton = container.querySelector(
      '[data-action="clear-filters"]',
    );
    if (clearButton && form) {
      clearButton.addEventListener("click", () => {
        form.reset();

        if (gpaSlider) {
          gpaSlider.value = "0.0";
          const valueDisplay =
            gpaSlider.parentElement.querySelector(".gpa-value-display");
          if (valueDisplay) {
            valueDisplay.textContent = "0.0";
          }
          gpaSlider.dispatchEvent(new Event("input", { bubbles: true }));
          gpaSlider.dispatchEvent(new Event("change", { bubbles: true }));
        }

        searchInputs.forEach((input) => {
          input.value = "";
          input.dispatchEvent(new Event("keyup"));
        });

        updateActiveState();
      });
    }

    if (form) {
      form.addEventListener("change", updateActiveState);
      form.addEventListener("input", updateActiveState);
    }

    updateActiveState();
  });
});
