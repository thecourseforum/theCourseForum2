/*
 * Cascading dropdown data population for the "new review" form
 * in review.py and reviews/new.html
 * Author: j-alicia-long, 11/22/2020
*/

// Executed when DOM is ready
jQuery(function($) {
    // Clear & disable sequenced dropdowns
    clearDropdown("#subject");
    clearDropdown("#courseID");
    clearDropdown("#instructor");
    clearDropdown("#semester");
    // Enable subject selector, disable the following
    $("#subject").prop("disabled", false);
    $("#courseID").prop("disabled", true);
    $("#instructor").prop("disabled", true);
    $("#semester").prop("disabled", true);

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
                text: subdept.mnemonic
            }).appendTo("#subject");
        });
        return this;
    });

    // Fetch course data on subject select
    $("#subject").change(function() {
        // Clear & disable sequenced dropdowns
        clearDropdown("#courseID");
        clearDropdown("#instructor");
        clearDropdown("#semester");
        // Enable course selector, disable the following
        $("#courseID").prop("disabled", false);
        $("#instructor").prop("disabled", true);
        $("#semester").prop("disabled", true);

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
                }).appendTo("#courseID");
            });
            return this;
        });
    });

    // Fetch instructor data on course select
    $("#courseID").change(function() {
        // Clear & disable sequenced dropdowns
        clearDropdown("#instructor");
        clearDropdown("#semester");
        // Enable instructor selector, disable the following
        $("#instructor").prop("disabled", false);
        $("#semester").prop("disabled", true);

        // Fetch instructor data from API, based on selected course
        var pageSize = "1000";
        var instrEndpoint = `/api/instructors/?course=${courseID}` +
            `&page_size=${pageSize}`;
        $.getJSON(instrEndpoint, function(data) {
            clearDropdown("#instructor"); // Empty dropdown

            // Generate option tags
            $.each(data.results, function(i, instr) {
                $("<option />", {
                    val: instr.id,
                    text: instr.first_name + " " + instr.last_name
                }).appendTo("#instructor");
            });
            return this;
        });
    });

    // Fetch semester data on instructor select
    $("#instructor").change(function() {
        // Clear & disable sequenced dropdowns
        clearDropdown("#semester");
        // Enable semester selector, disable the following
        $("#semester").prop("disabled", false);

        // Fetch all semester data from API
        var courseID = $("#courseID").val();
        var instrID = $("#instructor").val();
        var semEndpoint = `/api/semesters/?course=${courseID}&instructor=${instrID}`;
        $.getJSON(semEndpoint, function(data) {
            // Generate option tags
            $.each(data, function(i, semester) {
                // Note: API returns semester list in reverse chronological order
                // Most recent 5 years only
                if (semester.year > 2014) {
                    $("<option />", {
                        val: semester.id,
                        text: semester.season + " " + semester.year
                    }).appendTo("#semester");
                }
            });
            return this;
        });
    });
});

// Clears all dropdown options & adds a disabled default option
function clearDropdown(id) {
    $(id).empty();
    $(id).html("<option value='' disabled selected>Select...</option>");
}
