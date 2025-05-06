document.addEventListener("DOMContentLoaded", function () {
  // Determines if any filters (besides day ones) are active
  const filterInputs = document.querySelectorAll(
    '.dropdown-menu input[type="checkbox"]:not(.day-checkbox)',
  );
  const dayFilters = document.querySelectorAll(".day-checkbox");
  const filterButton = document.getElementById("filter-button");
  const timeFrom = document.getElementById("from_time");
  const timeTo = document.getElementById("to_time");
  const openSections = document.getElementById("open-sections");
  const minGpaSlider = document.getElementById("min-gpa-slider");
  const minGpaText = document.getElementById("min-gpa-text");
  const minGpaInput = document.getElementById("min-gpa-input");

  // Check if filters should be loaded from localStorage
  loadFiltersFromLocalStorage();

  // Check initial state (in case of page refresh with active filters)
  updateButtonState();

  // Add event listeners to all filter inputs
  [...filterInputs, ...dayFilters, openSections].forEach((input) => {
    input.addEventListener("change", function () {
      updateButtonState();
      saveFiltersToLocalStorage();
    });
  });

  [timeFrom, timeTo].forEach((input) => {
    input.addEventListener("input", function () {
      updateButtonState();
      saveFiltersToLocalStorage();
    });
  });

  // Min GPA slider and text input synchronization
  minGpaSlider.addEventListener("input", function () {
    const value = parseFloat(this.value).toFixed(1); // Ensures clean decimal
    minGpaText.value = value;
    minGpaInput.value = value;
    updateButtonState();
    saveFiltersToLocalStorage();
  });

  minGpaText.addEventListener("change", function () {
    // Only update if valid number
    let value = parseFloat(this.value);

    // Validate and constrain the value
    if (isNaN(value)) {
      value = 0.0; // Default to 0.0 if invalid
    } else {
      // Keep value between 0 and 4
      value = Math.max(0, Math.min(4, value));
      // Round to nearest 0.1
      value = Math.round(value * 10) / 10;
    }

    // Update all inputs with the cleaned value
    this.value = value.toFixed(1);
    minGpaSlider.value = value;
    minGpaInput.value = value;
    updateButtonState();
    saveFiltersToLocalStorage();
  });

  // Allow enter key on min-gpa-text to apply the filter
  minGpaText.addEventListener("keyup", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();
      this.blur(); // Remove focus to trigger change event
      document.querySelector('button[type="submit"]').click(); // Submit the form
    }
  });

  // Save current filter state to localStorage
  function saveFiltersToLocalStorage() {
    // Get selected subdepartments
    const selectedSubdepts = Array.from(
      document.querySelectorAll(".form-check-subjects:checked"),
    ).map((input) => input.value);

    // Get selected disciplines
    const selectedDisciplines = Array.from(
      document.querySelectorAll(".form-check-disciplines:checked"),
    ).map((input) => input.value);

    // Get selected weekdays
    const selectedWeekdays = Array.from(
      document.querySelectorAll(".day-checkbox:checked"),
    ).map((input) => input.value);

    // Create filters object
    const filters = {
      subdepartments: selectedSubdepts,
      disciplines: selectedDisciplines,
      weekdays: selectedWeekdays,
      from_time: timeFrom ? timeFrom.value : "",
      to_time: timeTo ? timeTo.value : "",
      open_sections: openSections ? openSections.checked : false,
      min_gpa: minGpaInput ? parseFloat(minGpaInput.value || "0.0") : 0.0,
    };

    // Save to localStorage
    localStorage.setItem("search_filters", JSON.stringify(filters));
  }

  // Load filters from localStorage
  function loadFiltersFromLocalStorage() {
    const savedFilters = localStorage.getItem("search_filters");
    if (!savedFilters) return;

    try {
      const filters = JSON.parse(savedFilters);

      // Set subdepartments
      if (filters.subdepartments && filters.subdepartments.length) {
        filters.subdepartments.forEach((mnemonic) => {
          const input = document.getElementById(`subject-${mnemonic}`);
          if (input) input.checked = true;
        });
      }

      // Set disciplines
      if (filters.disciplines && filters.disciplines.length) {
        filters.disciplines.forEach((name) => {
          const input = document.getElementById(
            `discipline-${name.toLowerCase().replace(/\s+/g, "-")}`,
          );
          if (input) input.checked = true;
        });
      }

      // Set weekdays
      if (filters.weekdays && filters.weekdays.length) {
        filters.weekdays.forEach((day) => {
          const dayMap = {
            MON: "monday",
            TUE: "tuesday",
            WED: "wednesday",
            THU: "thursday",
            FRI: "friday",
          };
          const input = document.getElementById(dayMap[day]);
          if (input) input.checked = true;
        });
        updateWeekdays(); // Update the hidden input
      }

      // Set time values
      if (timeFrom && filters.from_time) timeFrom.value = filters.from_time;
      if (timeTo && filters.to_time) timeTo.value = filters.to_time;

      // Set open sections
      if (openSections && filters.open_sections !== undefined) {
        openSections.checked = filters.open_sections;
      }

      // Set min GPA
      if (filters.min_gpa !== undefined) {
        const gpaValue = parseFloat(filters.min_gpa).toFixed(1);
        if (minGpaSlider) minGpaSlider.value = gpaValue;
        if (minGpaText) minGpaText.value = gpaValue;
        if (minGpaInput) minGpaInput.value = gpaValue;
      }
    } catch (e) {
      console.error("Error loading filters from localStorage:", e);
    }
  }

  // Checks for active filters or inactive day filters to determine button state
  function updateButtonState() {
    const hasActiveFilters =
      Array.from(filterInputs).some((input) => input.checked) ||
      Array.from(dayFilters).some((input) => input.checked) ||
      (timeFrom && timeFrom.value !== "") ||
      (timeTo && timeTo.value !== "") ||
      (openSections && openSections.checked) ||
      (minGpaInput && parseFloat(minGpaInput.value) !== 0.0);

    if (hasActiveFilters) {
      filterButton.classList.add("filter-active");
    } else {
      filterButton.classList.remove("filter-active");
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

  // Generic function for filtering items
  function setupSearch(searchInput, itemsSelector) {
    const items = document.querySelectorAll(itemsSelector);
    searchInput.addEventListener("input", function (e) {
      const searchTerm = e.target.value.toLowerCase();
      items.forEach((item) => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(searchTerm) ? "" : "none";
      });
    });
  }

  // Setup search functionality
  setupSearch(
    document.getElementById("subject-search"),
    ".subject-list .form-check",
  );
  setupSearch(
    document.getElementById("discipline-search"),
    ".discipline-list .form-check",
  );

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

  // Setup reordering for subjects and disciplines
  function setupReordering(checkboxSelector, containerSelector) {
    document.querySelectorAll(checkboxSelector).forEach((checkbox) => {
      checkbox.addEventListener("change", () => {
        reorderList(containerSelector, checkboxSelector);
      });
    });
    // Call reorder on page load in case some items are selected by default
    reorderList(containerSelector, checkboxSelector);
  }

  setupReordering(".form-check-subjects", ".subject-list");
  setupReordering(".form-check-disciplines", ".discipline-list");

  const resetButton = document.querySelector('button[type="reset"]');
  resetButton.addEventListener("click", function (e) {
    e.preventDefault(); // Prevent default reset behavior
    clearFilters();
  });

  // Function to clear all filters
  function clearFilters() {
    // Reset checkboxes
    document.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
      checkbox.checked = false;
    });

    // Clear subject search
    document.getElementById("subject-search").value = "";
    document.querySelectorAll(".subject-list .form-check").forEach((item) => {
      item.style.display = ""; // Show all subjects
    });

    // Clear discipline search
    document.getElementById("discipline-search").value = "";
    document
      .querySelectorAll(".discipline-list .form-check")
      .forEach((item) => {
        item.style.display = ""; // Show all disciplines
      });

    // Set time inputs to empty
    timeFrom.value = "";
    timeTo.value = "";

    // Reset min GPA to default value of 0.0
    if (minGpaSlider) minGpaSlider.value = 0.0;
    if (minGpaText) minGpaText.value = 0.0;
    if (minGpaInput) minGpaInput.value = 0.0;

    updateWeekdays();
    updateButtonState();

    // Clear localStorage filters
    localStorage.removeItem("search_filters");

    // Reorder lists after clearing filters
    reorderList(".subject-list", ".form-check-subjects");
    reorderList(".discipline-list", ".form-check-disciplines");
  }

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
      saveFiltersToLocalStorage();
    });
  });

  // Update weekdays on checkbox change
  document.querySelectorAll(".day-checkbox").forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      updateWeekdays();
      updateButtonState();
      saveFiltersToLocalStorage();
    });
  });

  // Initialize weekdays
  updateWeekdays();

  // Clear filters when window is resized to mobile view
  window.addEventListener("resize", function () {
    if (window.innerWidth <= 992) {
      clearFilters();
    }
  });
});
