document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".search-bar-container").forEach((container) => {
    const toggle = container.querySelector(".search-bar__filter-trigger");
    const dropdown = container.querySelector(".search-filters");
    const form = container.querySelector("form");
    const gpaSlider = container.querySelector('input[name="min_gpa"]');

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
