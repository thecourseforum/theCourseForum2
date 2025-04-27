/*
 * Dropdown data population for club reviews in the "new review" form
 */

// Executed when DOM is ready
jQuery(function ($) {
  /* Initial setup */
  // Clear & disable dropdowns
  clearDropdown("#category");
  clearDropdown("#club");
  clearDropdown("#semester");

  // Check for URL params and handle prefilling
  const params = window.location.search;
  let clubId = null;

  if (params.length > 0) {
    // Parse club ID from URL
    const urlParams = new URLSearchParams(params);
    
    // Only try to parse club parameter if it exists
    if (urlParams.has("club")) {
      clubId = parseInt(urlParams.get("club"));

      // If we have a club ID, fetch the club details to get its category
      if (clubId) {
        fetchClubDetails(clubId);
      }
    }
  }

  // Enable category dropdown, which is the first in sequence
  $("#category").prop("disabled", false);
  $("#club").prop("disabled", true);
  $("#semester").prop("disabled", true);

  // Fetch all club categories from API
  const categoryEndpoint = "/api/club-categories/";
  $.ajax({
    url: categoryEndpoint,
    dataType: "json",
    success: function (data) {
      if (data.results) {
        // Sort categories alphabetically by name
        data.results.sort(function (a, b) {
          return a.name.localeCompare(b.name);
        });

        // Generate option tags
        $.each(data.results, function (i, category) {
          $("<option />", {
            value: category.id,
            text: category.name,
          }).appendTo("#category");
        });
      } else if (Array.isArray(data)) {
        // Sort categories alphabetically by name
        data.sort(function (a, b) {
          return a.name.localeCompare(b.name);
        });

        // Generate option tags
        $.each(data, function (i, category) {
          $("<option />", {
            value: category.id,
            text: category.name,
          }).appendTo("#category");
        });
      }

      // Signal that categories have loaded
      $(document).trigger("categories-loaded");
    },
    error: function (xhr, status, error) {
      console.error("Error loading categories:", error);
      $("<option />").text("Error loading categories").appendTo("#category");

      // Even on error, trigger the event
      $(document).trigger("categories-loaded");
    },
  });

  /* Fetch club data on category select */
  $("#category").change(function () {
    // Clear club dropdown
    clearDropdown("#club");
    clearDropdown("#semester");
    $("#club").prop("disabled", true);
    $("#semester").prop("disabled", true);

    const categoryId = $(this).val();
    if (!categoryId) {
      return;
    }

    // Fetch clubs for the selected category
    const clubEndpoint = `/api/clubs/?category=${categoryId}`;
    $.ajax({
      url: clubEndpoint,
      dataType: "json",
      success: function (data) {
        if (data.results && data.results.length > 0) {
          // Generate option tags from results
          $.each(data.results, function (i, club) {
            $("<option />", {
              value: club.id,
              text: club.name,
              selected: club.id === clubId,
            }).appendTo("#club");
          });
        } else if (Array.isArray(data) && data.length > 0) {
          // Generate option tags from array
          $.each(data, function (i, club) {
            $("<option />", {
              value: club.id,
              text: club.name,
              selected: club.id === clubId,
            }).appendTo("#club");
          });
        } else {
          // No clubs found
          $("<option />").text("No clubs found").appendTo("#club");
        }

        // Enable the club dropdown
        $("#club").prop("disabled", false);

        // Signal that clubs have loaded
        $(document).trigger("clubs-loaded");
      },
      error: function (xhr, status, error) {
        console.error("Error loading clubs:", error);
        $("<option />").text("Error loading clubs").appendTo("#club");
        $("#club").prop("disabled", false);

        // Even on error, trigger the event
        $(document).trigger("clubs-loaded");
      },
    });
  });

  /* Add club select handler to load semesters when a club is selected */
  $("#club").change(function() {
    // Clear semester dropdown
    clearDropdown("#semester");
    $("#semester").prop("disabled", true);
    
    // Only proceed if we have a club selected
    const clubId = $(this).val();
    if (!clubId) {
      return;
    }
    
    // Now load semesters since a club is selected
    loadSemesters();
  });

  // Fetch club details to get its category, then trigger category selection
  function fetchClubDetails(clubId) {
    $.ajax({
      url: `/api/clubs/${clubId}/`,
      dataType: "json",
      success: function (club) {
        if (club && club.category) {
          // Wait for categories to load using a custom event
          $(document).one("categories-loaded", function () {
            // Select the category
            $("#category").val(club.category.id).trigger("change");

            // Wait for clubs to load using a custom event
            $(document).one("clubs-loaded", function () {
              // Now select the club
              $("#club").val(clubId).trigger("change");
            });
          });

          // If categories are already loaded, manually trigger the event
          if ($("#category option").length > 1) {
            $(document).trigger("categories-loaded");
          }
        }
      },
      error: function (xhr, status, error) {
        console.error("Error loading club details:", error);
      },
    });
  }

  // Add club-specific hidden fields before form submission
  $("#reviewForm").submit(function (e) {
    // Don't interfere with original submission flow
    // Just add the necessary hidden fields

    // Get the current club id
    const clubId = $("#club").val();

    if (clubId) {
      // Remove any existing hidden fields
      $("#hidden-club-field").remove();
      $("#hidden-mode-field").remove();

      // Add club ID field
      $("<input>")
        .attr({
          type: "hidden",
          id: "hidden-club-field",
          name: "club",
          value: clubId,
        })
        .appendTo("#reviewForm");

      // Add mode field
      $("<input>")
        .attr({
          type: "hidden",
          id: "hidden-mode-field",
          name: "mode",
          value: "clubs",
        })
        .appendTo("#reviewForm");
    }

    // Let the original submit handler continue
  });

  // Review Progress Bar - Add word count functionality for the review text area
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

/* Load semesters */
function loadSemesters() {
  clearDropdown("#semester");
  $("#semester").prop("disabled", true);

  // Fetch semester data
  const semEndpoint = "/api/semesters/";
  $.ajax({
    url: semEndpoint,
    dataType: "json",
    success: function (data) {
      if (data.results && data.results.length > 0) {
        // Generate option tags from results
        $.each(data.results, function (i, semester) {
          $("<option />", {
            value: semester.id,
            text: semester.season + " " + semester.year,
          }).appendTo("#semester");
        });
      } else if (Array.isArray(data) && data.length > 0) {
        // Generate option tags from array
        $.each(data, function (i, semester) {
          $("<option />", {
            value: semester.id,
            text: semester.season + " " + semester.year,
          }).appendTo("#semester");
        });
      } else {
        // No semesters found
        $("<option />").text("No semesters found").appendTo("#semester");
      }

      // Enable the semester dropdown
      $("#semester").prop("disabled", false);
    },
    error: function (xhr, status, error) {
      console.error("Error loading semesters:", error);
      $("<option />").text("Error loading semesters").appendTo("#semester");
      $("#semester").prop("disabled", false);
    },
  });
}

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
