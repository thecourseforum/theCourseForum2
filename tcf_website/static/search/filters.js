document.addEventListener("DOMContentLoaded", function () {
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
  }

  function setCookie(name, value, days) {
    const date = new Date();
    date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
    const expires = `expires=${date.toUTCString()}`;
    document.cookie = `${name}=${value};${expires};path=/`;
  }

  // Determines if any filters (besides day ones) are active
  const filterInputs = document.querySelectorAll(
    '.dropdown-menu input[type="checkbox"]:not(.day-checkbox)',
  );
  const dayFilters = document.querySelectorAll(".day-checkbox");
  const filterButton = document.getElementById("filter-button");
  const timeFrom = document.getElementById("from_time");
  const timeTo = document.getElementById("to_time");
  const openSections = document.getElementById("open-sections");

  // Check initial state (in case of page refresh with active filters)
  updateButtonState();

  filterInputs.forEach((input) => {
    input.addEventListener("change", updateButtonState);
  });

  dayFilters.forEach((input) => {
    input.addEventListener("change", updateButtonState);
  });

  timeFrom.addEventListener("input", updateButtonState);
  timeTo.addEventListener("input", updateButtonState);

  openSections.addEventListener("change", updateButtonState);

  // Checks for active filters or inactive day filters to determine button state
  function updateButtonState() {
    const activeFilters = Array.from(filterInputs).filter(
      (input) => input.checked,
    );
    const activeDayFilters = Array.from(dayFilters).filter(
      (input) => input.checked,
    );

    let timeFromChanged = false;
    let timeToChanged = false;
    let openSectionsChanged = false;

    if (timeFrom.value) {
      timeFromChanged = timeFrom.value !== "";
    }
    if (timeTo.value) {
      timeToChanged = timeTo.value !== "";
    }

    if (openSections.checked) {
      openSectionsChanged = true;
    }

    if (
      activeFilters.length > 0 ||
      activeDayFilters.length > 0 ||
      timeFromChanged ||
      timeToChanged ||
      openSectionsChanged
    ) {
      filterButton.classList.add("filter-active");
      filterButton.textContent = "Filters Active";
    } else {
      filterButton.classList.remove("filter-active");
      filterButton.textContent = "Filters";
    }
  }

  const dropdown = document.getElementById("filter-dropdown");
  const searchInput = document.querySelector(
    ".form-control.border.border-right-0",
  );

  searchInput.addEventListener("click", function (event) {
    event.stopPropagation();
  });

  // Only prevent dropdown from closing when clicking inside
  dropdown.addEventListener("click", function (event) {
    event.stopPropagation();
  });

  // Add subject search functionality
  const subjectSearch = document.getElementById("subject-search");
  const subjectItems = document.querySelectorAll(".subject-list .form-check");

  subjectSearch.addEventListener("input", function (e) {
    const searchTerm = e.target.value.toLowerCase();

    subjectItems.forEach((item) => {
      const text = item.textContent.toLowerCase();
      item.style.display = text.includes(searchTerm) ? "" : "none";
    });
  });

  // Add discipline search functionality
  const disciplineSearch = document.getElementById("discipline-search");
  const disciplineItems = document.querySelectorAll(
    ".discipline-list .form-check",
  );

  disciplineSearch.addEventListener("input", function (e) {
    const searchTerm = e.target.value.toLowerCase();

    disciplineItems.forEach((item) => {
      const text = item.textContent.toLowerCase();
      item.style.display = text.includes(searchTerm) ? "" : "none";
    });
  });

  // Reordering function to pin selected checkboxes to the top
  function reorderList(containerSelector, checkboxSelector) {
    const container = document.querySelector(containerSelector);
    if (!container) return;
    const items = Array.from(container.children);
    items.sort((a, b) => {
      const aCheckbox = a.querySelector(checkboxSelector);
      const bCheckbox = b.querySelector(checkboxSelector);

      // Check if one is selected and the other is not
      if (aCheckbox.checked && !bCheckbox.checked) return -1;
      if (!aCheckbox.checked && bCheckbox.checked) return 1;

      // If both are either checked or unchecked, sort alphabetically by label text
      const aLabelText = a
        .querySelector("label")
        .textContent.trim()
        .toLowerCase();
      const bLabelText = b
        .querySelector("label")
        .textContent.trim()
        .toLowerCase();
      return aLabelText.localeCompare(bLabelText);
    });
    // Clear and reappend in new order
    container.innerHTML = "";
    items.forEach((item) => container.appendChild(item));
  }

  // Add event listeners to re-sort subjects whenever a subject checkbox changes
  document.querySelectorAll(".form-check-subjects").forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      reorderList(".subject-list", ".form-check-subjects");
    });
  });

  // Add event listeners to re-sort disciplines whenever a discipline checkbox changes
  document.querySelectorAll(".form-check-disciplines").forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      reorderList(".discipline-list", ".form-check-disciplines");
    });
  });

  // Call reorder on page load in case some items are selected by default
  reorderList(".subject-list", ".form-check-subjects");
  reorderList(".discipline-list", ".form-check-disciplines");

  const resetButton = document.querySelector('button[type="reset"]');
  resetButton.addEventListener("click", function (e) {
    e.preventDefault(); // Prevent default reset behavior

    // Reset checkboxes
    document.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
      checkbox.checked = false; // Set days to checked by default
    });

    // Clear subject search
    document.getElementById("subject-search").value = "";
    document.querySelectorAll(".subject-list .form-check").forEach((item) => {
      item.style.display = ""; // Show all subjects
    });

    // Set time inputs to empty
    document.getElementById("from_time").value = "";
    document.getElementById("to_time").value = "";

    updateWeekdays();
    updateButtonState();

    // Reorder lists after clearing filters (so any selected items, if any, are sorted correctly)
    reorderList(".subject-list", ".form-check-subjects");
    reorderList(".discipline-list", ".form-check-disciplines");
  });

  // Add weekdays handling
  function updateWeekdays() {
    const checkedDays = Array.from(
      document.querySelectorAll(".day-checkbox:checked"),
    )
      .map((cb) => cb.value)
      .join("-");
    document.getElementById("weekdays-input").value = checkedDays;
  }

  // Updates weekdays if div of checkbox is clicked
  document.querySelectorAll(".form-check-inline").forEach((container) => {
    container.addEventListener("click", (event) => {
      const checkbox = container.querySelector(".day-checkbox");
      if (event.target === checkbox || event.target.closest("label")) {
        return;
      }
      checkbox.checked = !checkbox.checked;
      checkbox.dispatchEvent(new Event("change"));
      updateWeekdays();
      updateButtonState();
    });
  });

  // Update weekdays on checkbox change
  document.querySelectorAll(".day-checkbox").forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      updateWeekdays();
      updateButtonState();
    });
  });

  // Initialize weekdays
  updateWeekdays();

  // Updates filter button
  updateButtonState();
});
