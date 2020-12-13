/*
 * Dropdown data population for the course-instructor page
 * Author: j-alicia-long, 12/13/2020
*/

// Executed when DOM is ready
jQuery(function($) {

    /*** Fetch instructor data for given course ***/
    // var courseID - From global var in template
    var pageSize = "1000";
    var instrEndpoint = `/api/instructors/?course=${courseID}` +
        `&page_size=${pageSize}`;
    $.getJSON(instrEndpoint, function(data) {
        console.log(data);
        // Generate dropdown links
        $.each(data.results, function(i, instr) {
            $("<a />", {
                id: `instr-${instr.id}`,
                class: "dropdown-item",
                href: `/course/${courseID}/${instr.id}`,
                text: instr.first_name + " " + instr.last_name
            }).appendTo("#instructor");
        });
        return this;
    })
    .done(function() {
      // Enable instructor selector
      $("#instructor").prop("disabled", false);
    });
});
