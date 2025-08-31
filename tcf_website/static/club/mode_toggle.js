// Common mode toggle functionality
document.addEventListener("DOMContentLoaded", function () {
  // For radio button toggle (searchbar)
  const radioToggle = document.querySelector(".mode-toggle");
  if (radioToggle) {
    const coursesRadio = document.getElementById("search-mode-courses");
    const clubsRadio = document.getElementById("search-mode-clubs");

    // Abort early if the expected inputs are missing
    if (!coursesRadio || !clubsRadio) {
      console.error(
        "mode_toggle.js: Could not find expected #search-mode-(courses|clubs) radios.",
      );
      return;
    }

    const filterButtonElement = document.getElementById("filter-button");

    // Find search input element
    const searchInput = document.querySelector('input[type="search"][name="q"]');

    // Update both filter button state and search placeholder
    function updateSearchbarState() {
      // Update filter button if it exists
      if (filterButtonElement) {
        if (clubsRadio.checked) {
          filterButtonElement.disabled = true;
          filterButtonElement.setAttribute("aria-disabled", "true");
          filterButtonElement.classList.add("disabled");
        } else {
          filterButtonElement.disabled = false;
          filterButtonElement.setAttribute("aria-disabled", "false");
          filterButtonElement.classList.remove("disabled");
        }
      }

      // Update search input placeholder if it exists
      if (searchInput) {
        if (clubsRadio.checked) {
          searchInput.placeholder = "Search for a club...";
        } else {
          searchInput.placeholder = "Search for a class or professor...";
        }
      }
    }

    // Set initial state
    updateSearchbarState();

    // Listen for changes
    coursesRadio.addEventListener("change", updateSearchbarState);
    clubsRadio.addEventListener("change", updateSearchbarState);

    // Remove no-transition class after page load to enable animations
    setTimeout(function () {
      radioToggle.classList.remove("no-transition");
    }, 100);
  }
});
