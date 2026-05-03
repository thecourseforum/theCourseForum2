function populateDropdown(dropdownID) {
  /* Fetch semester data for Answer dropdown */
  // Clear & disable sequenced dropdowns
  clearDropdown(dropdownID);
  const selectedSemID = parseInt(dropdownID.split("-")[1]);

  const paramsArr = window.location.pathname.split("/");

  // Fetch all semester data from API
  const course = paramsArr[2];
  const instrID = paramsArr[3];
  const semEndpoint = `/api/semesters/?course=${course}&instructor=${instrID}`;
  $.getJSON(semEndpoint, function (data) {
    // Generate option tags
    if (data.length === 0) {
      $("#ask-question-button").addClass("disabled");
      $(".answerQuestionBtn").addClass("disabled");
    } else {
      $.each(data, function (i, semester) {
        $("<option />", {
          val: semester.id,
          text: semester.season + " " + semester.year,
        }).appendTo(dropdownID);

        if (selectedSemID === semester.id) {
          $(dropdownID).val(semester.id);
        }
      });
    }
    return this;
  }).done(function () {
    // Enable semester selector
    $(dropdownID).prop("disabled", false);
  });
}

jQuery(function ($) {
  // Get all dropdown ids in the semester dropdown class for edit answer forms, clear and populate each
  const ids = $(".semester-dropdown")
    .map(function (_, x) {
      return "#".concat(x.id);
    })
    .get();
  ids.forEach((item) => populateDropdown(item));
});

$(document).ready(function () {
  $(document).on("click", "#answerQuestionBtn", function () {
    const questionId = $(this).data("id");
    $("#answerForm #questionInput").val(questionId);
  });

  $("#answerForm").submit(function (e) {
    $("#submitBtn").prop("disabled", true);
  });
});

// Clears all dropdown options & adds a disabled default option
function clearDropdown(id) {
  $(id).empty();
  $(id).html("<option value='' disabled selected>Select...</option>");
}
