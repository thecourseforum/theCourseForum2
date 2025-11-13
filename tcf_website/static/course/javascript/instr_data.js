/*
 * Dropdown data population for the course-instructor page
 * Author: j-alicia-long, 12/13/2020
 */

// Executed when DOM is ready
jQuery(function ($) {
  let instructorsLoaded = false;
  let isLoading = false;

  /* Fetch instructor data for given course and semester - only when dropdown is clicked */
  function loadInstructors() {
    // Don't load if already loaded or currently loading
    if (instructorsLoaded || isLoading) {
      return;
    }

    isLoading = true;

    const pageSize = "100";
    const instrEndpoint =
      `/api/instructors/?course=${window.courseID}&semester=${window.latestSemesterID}` +
      `&page_size=${pageSize}`;
    // window.courseID and window.latestSemesterID are from global vars in template
    $.getJSON(instrEndpoint, function (data) {
      // Handle both paginated response {results: [...]} and direct array [...]
      const instructors = Array.isArray(data) ? data : data.results || [];

      // Generate dropdown links
      $.each(instructors, function (i, instr) {
        $("<a />", {
          id: `instr-${instr.id}`,
          class: "dropdown-item",
          href: `/course/${window.courseID}/${instr.id}`,
          text: instr.last_name + ", " + instr.first_name,
        }).appendTo("#instructorMenu");
      });

      instructorsLoaded = true;
      isLoading = false;
      return this;
    })
      .done(function () {
        // Enable instructor selector
        $("#instructorMenu").prop("disabled", false);
      })
      .fail(function () {
        isLoading = false;
      });
  }

  // Load instructors when dropdown is clicked/opened
  $("#dropdownMenuLink").on("click", loadInstructors);
  $("#dropdownMenuLink").on("show.bs.dropdown", loadInstructors);
});
