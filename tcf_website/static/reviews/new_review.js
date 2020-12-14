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

    /* Course Rating Slider Inputs */
    // Instructor Rating
    $("#instructorRating2").val($("#instructorRating").val());
    $("#instructorRating").change(function() {
        $("#instructorRating2").val($("#instructorRating").val());
    });
    $("#instructorRating2").change(function() {
        $("#instructorRating").val($("#instructorRating2").val());
    });

    // Enjoyability
    $("#enjoyability2").val($("#enjoyability").val());
    $("#enjoyability").change(function() {
        $("#enjoyability2").val($("#enjoyability").val());
    });
    $("#enjoyability2").change(function() {
        $("#enjoyability").val($("#enjoyability2").val());
    });

    // Difficulty
    $("#difficulty2").val($("#difficulty").val());
    $("#difficulty").change(function() {
        $("#difficulty2").val($("#difficulty").val());
    });
    $("#difficulty2").change(function() {
        $("#difficulty").val($("#difficulty2").val());
    });

    // Recommendability
    $("#recommendability2").val($("#recommendability").val());
    $("#recommendability").change(function() {
        $("#recommendability2").val($("#recommendability").val());
    });
    $("#recommendability2").change(function() {
        $("#recommendability").val($("#recommendability2").val());
    });
});

// Clears all dropdown options & adds a disabled default option
function clearDropdown(id) {
    $(id).empty();
    $(id).html("<option value='' disabled selected>Select...</option>");
}
