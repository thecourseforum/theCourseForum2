document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("search-input");
  if (!searchInput) return;

  // Create container for autocomplete suggestions
  const suggestionsContainer = document.createElement("div");
  suggestionsContainer.classList.add("autocomplete-suggestions");

  const searchbarWrapper = searchInput.closest(".searchbar-wrapper");
  if (searchbarWrapper) {
    searchbarWrapper.appendChild(suggestionsContainer);
  } else {
    return;
  }

  let debounceTimeout = null;
  let currentRequestController = null;

  // Debounce to reduce API calls
  function debounce(func, delay) {
    return function (...args) {
      clearTimeout(debounceTimeout);
      debounceTimeout = setTimeout(() => func(...args), delay);
    };
  }

  async function fetchSuggestions(query) {
    if (!query.trim()) {
      clearSuggestions();
      return;
    }

    // Cancel previous request if still in-flight
    if (currentRequestController) {
      currentRequestController.abort();
    }

    currentRequestController = new AbortController();

    try {
      const response = await fetch(
        `/api/autocomplete/?q=${encodeURIComponent(query)}`,
        { signal: currentRequestController.signal },
      );

      if (!response.ok) {
        clearSuggestions();
        return;
      }

      const data = await response.json();
      renderSuggestions(data);
    } catch (error) {
      if (error.name !== "AbortError") {
        console.error("Autocomplete fetch error:", error);
      }
      clearSuggestions();
    }
  }

  // Render suggestions
  function renderSuggestions(data) {
    suggestionsContainer.innerHTML = "";

    const hasCourses = data?.courses?.length > 0;
    const hasInstructors = data?.instructors?.length > 0;

    if (!hasCourses && !hasInstructors) {
      suggestionsContainer.style.display = "none";
      return;
    }

    const MAX_RESULTS = 8;
    const courses = (data.courses || []).slice(0, MAX_RESULTS);
    const instructors = (data.instructors || []).slice(0, MAX_RESULTS);

    // Add group headers for clarity
    if (hasCourses) {
      const header = document.createElement("div");
      header.classList.add("autocomplete-header");
      header.textContent = "Courses";
      suggestionsContainer.appendChild(header);
    }

    // Courses first
    courses.forEach((course) => {
      const item = document.createElement("div");
      item.classList.add("autocomplete-item");
      item.style.cursor = "pointer";
      item.textContent = `${course.subdepartment} ${course.number} — ${course.title}`;
      item.addEventListener("click", () => {
        searchInput.value = `${course.subdepartment} ${course.number}`;
        clearSuggestions();
        if (searchInput.form) {
          searchInput.form.submit();
        }
      });
      suggestionsContainer.appendChild(item);
    });

    if (instructors.length > 0) {
      const header = document.createElement("div");
      header.classList.add("autocomplete-header");
      header.textContent = "Instructors";
      suggestionsContainer.appendChild(header);
    }

    // Instructor results
    instructors.forEach((instructor) => {
      const item = document.createElement("div");
      item.classList.add("autocomplete-item");
      item.style.cursor = "pointer";
      item.textContent = instructor.full_name;
      item.addEventListener("click", () => {
        searchInput.value = instructor.full_name;
        clearSuggestions();
        if (searchInput.form) {
          searchInput.form.submit();
        }
      });
      suggestionsContainer.appendChild(item);
    });

    suggestionsContainer.style.display = "block";
  }

  // Helper to clear dropdown
  function clearSuggestions() {
    suggestionsContainer.innerHTML = "";
    suggestionsContainer.style.display = "none";
  }

  // Hide dropdown when clicking outside
  document.addEventListener("click", (event) => {
    if (
      !suggestionsContainer.contains(event.target) &&
      event.target !== searchInput
    ) {
      clearSuggestions();
    }
  });

  // Debounced input listener
  searchInput.addEventListener(
    "input",
    debounce((event) => {
      fetchSuggestions(event.target.value);
    }, 250),
  );
});
