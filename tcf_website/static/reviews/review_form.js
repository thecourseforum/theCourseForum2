/*
 * Cascading dropdown data population for the "new review" form
 * in review.py and reviews/new.html
 * Author: j-alicia-long, 11/22/2020
*/

// Executed when DOM is ready
jQuery(function($) {
    // Fetch all semester data from API
    var semEndpoint = "http://localhost:8000/api/semesters/";
    $.getJSON(semEndpoint, function(data) {
        clearDropdown("#semester"); // Empty dropdown

        // Generate option tags
        $.each(data, function(i, semester) {
            // Most recent 5 years only
            if (semester.year > 2015) {
                $("<option />", {
                    val: semester.id,
                    text: semester.season + " " + semester.year
                }).appendTo("#semester");
            }
        });
        return this;
    });

    // Fetch all subdepartment data from API
    var subdeptEndpoint = "http://localhost:8000/api/subdepartments/";
    $.getJSON(subdeptEndpoint, function(data) {
        clearDropdown("#subject"); // Empty dropdown

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
        // Fetch course data from API, based on selected subdepartment
        var subdeptID = $("#subject").val();
        var pageSizeParam = "&page_size=1000";
        var courseEndpoint = "http://localhost:8000/api/courses/?subdepartment=" + subdeptID + pageSizeParam;
        $.getJSON(courseEndpoint, function(data) {
            clearDropdown("#courseID"); // Empty dropdown
            clearDropdown("#instructor"); //  Since courses are reloaded

            // Generate option tags
            $.each(data.results, function(i, course) {
                // 4-digit courseIDs only
                if (course.number > 1000) {
                    $("<option />", {
                        val: course.id,
                        text: course.number
                    }).appendTo("#courseID");
                }
            });
            return this;
        });
    });

    // Fetch instructor data on course select
    $("#courseID").change(function() {
        // Fetch instructor data from API, based on selected course
        var courseID = $("#courseID").val();
        var pageSizeParam = "&page_size=1000";
        var instrEndpoint = "http://localhost:8000/api/instructors/?section__course=" + courseID + pageSizeParam;
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
});

// Clears all dropdown options & adds a disabled default option
function clearDropdown(id) {
    $(id).empty();
    $(id).html("<option value='' disabled selected>[Select]</option>");
}
