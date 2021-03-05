/*
 * Cascading dropdown data population for the "new review" form
 * in review.py and reviews/new_review.html
 * Author: j-alicia-long, 11/22/2020
*/

// Executed when DOM is ready
jQuery(function($) {
    /* Fetch subject(subdepartment) data initially */
    // Clear & disable sequenced dropdowns
    clearDropdown("#subject");
    clearDropdown("#course");
    clearDropdown("#instructor");
    clearDropdown("#semester");

    // Fetch all subdepartment data from API
    var subdeptEndpoint = "/api/subdepartments/";
    $.getJSON(subdeptEndpoint, function(data) {
        // Sort departments alphabetically by mnemonic
        data.sort(function(a, b) {
            return a.mnemonic.localeCompare(b.mnemonic);
        });

        // Generate option tags
        $.each(data, function(i, subdept) {
            $("<option />", {
                val: subdept.id,
                text: subdept.mnemonic + " | " + subdept.name
            }).appendTo("#subject");
        });
        return this;
    })
        .done(function() { // Second callback
            // Enable subject selector, disable the following
            $("#subject").prop("disabled", false);
            $("#course").prop("disabled", true);
            $("#instructor").prop("disabled", true);
            $("#semester").prop("disabled", true);
        });

    /* Fetch course data on subject select */
    $("#subject").change(function() {
        // Clear & disable sequenced dropdowns
        clearDropdown("#course");
        clearDropdown("#instructor");
        clearDropdown("#semester");

        // Fetch course data from API, based on selected subdepartment
        var subdeptID = $("#subject").val();
        var pageSize = "1000";
        var courseEndpoint = `/api/courses/?subdepartment=${subdeptID}
                              &page_size=${pageSize}&recent`;
        $.getJSON(courseEndpoint, function(data) {
            // Generate option tags
            $.each(data.results, function(i, course) {
                $("<option />", {
                    val: course.id,
                    text: course.number + " | " + course.title
                }).appendTo("#course");
            });
            return this;
        })
            .done(function() {
                // Enable course selector, disable the following
                $("#course").prop("disabled", false);
                $("#instructor").prop("disabled", true);
                $("#semester").prop("disabled", true);
            });
    });

    /* Fetch instructor data on course select */
    $("#course").change(function() {
        // Clear & disable sequenced dropdowns
        clearDropdown("#instructor");
        clearDropdown("#semester");

        // Fetch instructor data from API, based on selected course
        var course = $("#course").val();
        var pageSize = "1000";
        var instrEndpoint = `/api/instructors/?course=${course}` +
            `&page_size=${pageSize}`;
        $.getJSON(instrEndpoint, function(data) {
            clearDropdown("#instructor"); // Empty dropdown

            // Generate option tags
            $.each(data.results, function(i, instr) {
                $("<option />", {
                    val: instr.id,
                    text: instr.last_name + ", " + instr.first_name
                }).appendTo("#instructor");
            });
            return this;
        })
            .done(function() {
                // Enable instructor selector, disable the following
                $("#instructor").prop("disabled", false);
                $("#semester").prop("disabled", true);
            });
    });

    /* Fetch semester data on instructor select */
    $("#instructor").change(function() {
        // Clear & disable sequenced dropdowns
        clearDropdown("#semester");

        // Fetch all semester data from API
        var course = $("#course").val();
        var instrID = $("#instructor").val();
        var semEndpoint = `/api/semesters/?course=${course}&instructor=${instrID}`;
        $.getJSON(semEndpoint, function(data) {
            // Generate option tags
            $.each(data, function(i, semester) {
                // Note: API returns semester list in reverse chronological order,
                // Most recent 5 years only
                $("<option />", {
                    val: semester.id,
                    text: semester.season + " " + semester.year
                }).appendTo("#semester");
            });
            return this;
        })
            .done(function() {
                // Enable semester selector
                $("#semester").prop("disabled", false);
            });
    });

    // Code for the progress bar
    $("#reviewtext").on("keyup keypress keydown", function() { // Need all these different events so it works truly dynamically
        // Used .trim() to remove leading and trailing spaces
        var review = $("#reviewtext").val().trim();
        var numberOfWords = countNumberOfWords(review);

        // Set the width of the bar to the what percent of 300 words the current review is
        $("#reviewprogressbar").width(1000 * (numberOfWords / 300));
        if (numberOfWords < 100) {
            // Originally a django progress bar with danger for red so need to remove that to change colors
            $("#reviewprogressbar").removeClass("progress-bar bg-danger");
            $("#reviewprogressbar").css("background-color", "#ffb3ba");
            $("#progressbarmessage").html("Your review is under 100 words. Aim for 300 or more!");
        } else if (numberOfWords >= 100 && numberOfWords < 200) {
            $("#reviewprogressbar").css("background-color", "#FFDAC1");
            $("#progressbarmessage").html("Good job getting to 100 words, keep going!");
        } else if (numberOfWords >= 200 && numberOfWords < 300) {
            $("#reviewprogressbar").css("background-color", "#fff5ba");
            $("#progressbarmessage").html("200 words! You're so close to the 300 mark!");
        } else if (numberOfWords >= 300) {
            $("#reviewprogressbar").css("background-color", "#B5EAD7");
            $("#progressbarmessage").html("Thank you for your in depth review. The tCF team and other users appreciate your effort!");
        }
    });
});

// Counts the number of words in a review
function countNumberOfWords(review) {
    if (review.length === 0 || typeof review !== "string") {
        return 0;
    }
    // Create an array of all the words
    var arrayOfWords = review.split(" ");

    // Used to keep track of all "words" with no letters in them
    var countNonAlphaWords = 0;

    // Iterate through all words and letters within the words
    for (var i = 0; i < arrayOfWords.length; i++) {
        // Tracks if the word is all non letter characters
        var allNonAlpha = true;
        for (var j = 0; j < arrayOfWords[i].length; j++) {
            if (arrayOfWords[i][j].toUpperCase() >= "A" && arrayOfWords[i][j].toUpperCase() <= "Z") {
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
