// Common mode toggle functionality
document.addEventListener("DOMContentLoaded", function () {
  // For radio button toggle (searchbar)
  const radioToggle = document.querySelector(".mode-toggle");
  if (radioToggle) {
    const coursesRadio = document.getElementById("search-mode-courses");
    const clubsRadio = document.getElementById("search-mode-clubs");
    const filterButtonElement = document.getElementById("filter-button");

    // If filter button exists, handle toggle state affecting filter button
    if (filterButtonElement) {
      function updateFilterButtonState() {
        if (clubsRadio.checked) {
          filterButtonElement.disabled = true;
          filterButtonElement.classList.add("disabled");
        } else {
          filterButtonElement.disabled = false;
          filterButtonElement.classList.remove("disabled");
        }
      }

      // Set initial state
      updateFilterButtonState();

      // Listen for changes
      coursesRadio.addEventListener("change", updateFilterButtonState);
      clubsRadio.addEventListener("change", updateFilterButtonState);
    }

    // Remove no-transition class after page load to enable animations
    setTimeout(function () {
      radioToggle.classList.remove("no-transition");
    }, 100);
  }
});
