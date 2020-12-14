/*
 * Dropdown data population for the course-instructor page
 * Author: j-alicia-long, 12/13/2020
*/

// Executed when DOM is ready
jQuery(function($) {
    /* Fetch instructor data for given course */
    var pageSize = "1000";
    var instrEndpoint = `/api/instructors/?course=${courseID}` +
        `&page_size=${pageSize}`;
    // var courseID is from global var in template
    $.getJSON(instrEndpoint, function(data) {
        // Generate dropdown links
        $.each(data.results, function(i, instr) {
            $("<a />", {
                id: `instr-${instr.id}`,
                class: "dropdown-item",
                href: `/course/${courseID}/${instr.id}`,
                text: instr.last_name + ", " + instr.first_name
            }).appendTo("#instructorMenu");
        });
        return this;
    })
        .done(function() {
            // Enable instructor selector
            $("#instructorMenu").prop("disabled", false);
        });
});
