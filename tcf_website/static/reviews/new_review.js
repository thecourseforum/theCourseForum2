/*
 * Cascading dropdown data population for the "new review" form
 * in review.py and reviews/new_review.html
 * Author: j-alicia-long, 11/22/2020
 */

// Executed when DOM is ready
jQuery(function ($) {
  /* Fetch subject(subdepartment) data initially */
  // Clear & disable sequenced dropdowns
  clearDropdown("#subject");
  clearDropdown("#course");
  clearDropdown("#instructor");
  clearDropdown("#semester");

  // If coming from the sidebar, params.length = 0
  // If coming from a course professor page, params.length > 0
  const params = window.location.search;
  let subdeptID, courseID, instructorID;

  // Use URLSearchParams to properly parse query parameters
  if (params.length > 0) {
    const urlParams = new URLSearchParams(params);

    // Only try to parse course parameters if they exist
    if (urlParams.has("subdept_id")) {
      subdeptID = parseInt(urlParams.get("subdept_id"));

      if (urlParams.has("course_id")) {
        courseID = parseInt(urlParams.get("course_id"));
      }

      if (urlParams.has("instr_id")) {
        instructorID = parseInt(urlParams.get("instr_id"));
      }
    }
  }

  // Fetch all subdepartment data from API
  const subdeptEndpoint = "/api/subdepartments/";
  $.getJSON(subdeptEndpoint, function (data) {
    // Sort departments alphabetically by mnemonic
    data.sort(function (a, b) {
      return a.mnemonic.localeCompare(b.mnemonic);
    });

    // Generate option tags
    $.each(data, function (i, subdept) {
      $("<option />", {
        val: subdept.id,
        text: subdept.mnemonic + " | " + subdept.name,
        // Check for autofill
        selected: subdept.id === subdeptID,
      }).appendTo("#subject");
      // Trigger change on autofill
      if (subdept.id === subdeptID) {
        $("#subject").trigger("change");
      }
    });
    return this;
  }).done(function () {
    // Second callback
    // Enable subject selector, disable the following
    $("#subject").prop("disabled", false);
    $("#course").prop("disabled", true);
    $("#instructor").prop("disabled", true);
    $("#semester").prop("disabled", true);
  });

  /* Fetch course data on subject select */
  $("#subject").change(function () {
    // Clear & disable sequenced dropdowns
    clearDropdown("#course");
    clearDropdown("#instructor");
    clearDropdown("#semester");

    // Fetch course data from API, based on selected subdepartment
    const subdeptID = $("#subject").val();
    const pageSize = "100";
    const courseEndpoint = `/api/courses/?subdepartment=${subdeptID}
                              &page_size=${pageSize}&recent`;
    $.getJSON(courseEndpoint, function (data) {
      // Generate option tags
      $.each(data, function (i, course) {
        $("<option />", {
          val: course.id,
          text: course.number + " | " + course.title,
          // Check for autofill
          selected: course.id === courseID,
        }).appendTo("#course");
        // Trigger change on autofill
        if (course.id === courseID) {
          $("#course").trigger("change");
        }
      });
      return this;
    }).done(function () {
      // Enable course selector, disable the following
      $("#course").prop("disabled", false);
      $("#instructor").prop("disabled", true);
      $("#semester").prop("disabled", true);
    });
  });

  /* Fetch semester data on course select */
  $("#course").change(function () {
    // Clear & disable sequenced dropdowns
    clearDropdown("#semester");
    clearDropdown("#instructor");

    // Fetch semester data from API, based on selected course
    const course = $("#course").val();
    const semEndpoint = `/api/semesters/?course=${course}`;
    $.getJSON(semEndpoint, function (data) {
      clearDropdown("#semester"); // Empty dropdown

      // Generate option tags
      $.each(data, function (i, semester) {
        // Note: API returns semester list in reverse chronological order,
        // Most recent 5 years only
        $("<option />", {
          val: semester.id,
          text: semester.season + " " + semester.year,
        }).appendTo("#semester");
      });
      return this;
    }).done(function () {
      // Enable semester selector, disable instructor
      $("#semester").prop("disabled", false);
      $("#instructor").prop("disabled", true);
    });
  });

  /* Fetch instructor data on semester select */
  $("#semester").change(function () {
    // Clear & disable instructor dropdown
    clearDropdown("#instructor");

    // Fetch instructor data from API, based on selected course and semester
    const course = $("#course").val();
    const semester = $("#semester").val();
    const pageSize = "100";
    const instrEndpoint =
      `/api/instructors/?course=${course}&semester=${semester}` + `&page_size=${pageSize}`;
    $.getJSON(instrEndpoint, function (data) {
      clearDropdown("#instructor"); // Empty dropdown

      // Generate option tags
      $.each(data, function (i, instr) {
        $("<option />", {
          val: instr.id,
          text: instr.last_name + ", " + instr.first_name,
          // Check for autofill
          selected: instr.id === instructorID,
        }).appendTo("#instructor");
        // Trigger change on autofill
        if (instr.id === instructorID) {
          $("#instructor").trigger("change");
        }
      });
      return this;
    }).done(function () {
      // Enable instructor selector
      $("#instructor").prop("disabled", false);
    });
  });

  // Review Progress Bar
  $("#reviewtext").on("keyup keypress keydown", function () {
    // Need all these different events so it works dynamically
    // Used .trim() to remove leading and trailing spaces
    const review = $("#reviewtext").val().trim();
    const numberOfWords = countNumberOfWords(review);
    const encouragedWordCount = 150;

    // Set the width of the bar to the what percent of the encouraged word count the current review is (Used an outer container's width to ensure it scales properly to mobile)
    $("#review-progressbar").width(
      $("#review-form-div").width() * (numberOfWords / encouragedWordCount),
    );

    // String Form of the number of words out of the encouraged word count
    const numberOfWordsInMessage =
      "(" +
      numberOfWords.toString() +
      "/" +
      encouragedWordCount.toString() +
      ")";

    // Different progress bar colors and messages depending on the current word count
    if (numberOfWords < encouragedWordCount / 3) {
      // Originally a django progress bar with danger for red so need to remove that to change colors
      $("#review-progressbar").removeClass("progress-bar bg-danger");
      $("#review-progressbar").css("background-color", "#FFB3BA");
      $("#progressbar-message").html(
        numberOfWordsInMessage +
          " Your review is under " +
          (encouragedWordCount / 3).toString() +
          " words. Aim for " +
          encouragedWordCount.toString() +
          " or more!",
      );
    } else if (
      numberOfWords >= encouragedWordCount / 3 &&
      numberOfWords < (2 * encouragedWordCount) / 3
    ) {
      $("#review-progressbar").css("background-color", "#FFDAC1");
      $("#progressbar-message").html(
        numberOfWordsInMessage +
          " Good job getting to " +
          (encouragedWordCount / 3).toString() +
          " words, keep going!",
      );
    } else if (
      numberOfWords >= (2 * encouragedWordCount) / 3 &&
      numberOfWords < encouragedWordCount
    ) {
      $("#review-progressbar").css("background-color", "#FFF5BA");
      $("#progressbar-message").html(
        numberOfWordsInMessage +
          " " +
          ((2 * encouragedWordCount) / 3).toString() +
          " words! You're so close to the " +
          encouragedWordCount.toString() +
          " mark!",
      );
    } else if (numberOfWords >= encouragedWordCount) {
      $("#review-progressbar").css("background-color", "#B5EAD7");
      $("#progressbar-message").html(
        numberOfWordsInMessage +
          " Thank you for your in depth review. The tCF team and other users appreciate your effort!",
      );
    }
  });
});

// Counts the number of words in a review
function countNumberOfWords(review) {
  if (review.length === 0 || typeof review !== "string") {
    return 0;
  }
  // Create an array of all the words
  const arrayOfWords = review.split(" ");

  // Used to keep track of all "words" with no letters in them
  let countNonAlphaWords = 0;

  // Iterate through all words and letters within the words
  for (let i = 0; i < arrayOfWords.length; i++) {
    // Tracks if the word is all non letter characters
    let allNonAlpha = true;
    for (let j = 0; j < arrayOfWords[i].length; j++) {
      if (
        arrayOfWords[i][j].toUpperCase() >= "A" &&
        arrayOfWords[i][j].toUpperCase() <= "Z"
      ) {
        allNonAlpha = false;
      }
    }
    if (allNonAlpha) {
      countNonAlphaWords++;
    }
  }
  // Computes the total word count by subtracting amount of "words" by "words" with no letters
  return arrayOfWords.length - countNonAlphaWords;
}

// Clears all dropdown options & adds a disabled default option
function clearDropdown(id) {
  $(id).empty();
  $(id).html("<option value='' disabled selected>Select...</option>");
}
