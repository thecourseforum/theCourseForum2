// Populate the dropdown options for the new question form
// Executed when DOM is ready
jQuery(function ($) {
    /* Fetch subject(subdepartment) data initially */
    // Clear & disable sequenced dropdowns
    clearDropdown("#major");
    //clearDropdown("#course");
    clearDropdown("#semester"); 

    const subdeptEndpoint = "/api/subdepartments/";
    //const courseEndpoint = "/api/courses/";
    const semesterEndpoint = "/api/semesters/";

    /* Fetch all data on major select */
    $.getJSON(subdeptEndpoint, function (data) {
        // Generate option tags
        $.each(data, function (i, subdepartment) {
            $("<option />", {
                val: subdepartment.id,
                text: subdepartment.mnemonic + " | " + subdepartment.name,
            }).appendTo("#major");
        }); 
        return this;
    });

    /*$.getJSON(courseEndpoint, function (data) {
        // Generate option tags
        $.each(data, function (i, course) {
            $("<option />", {
                val: course.id,
                text: course.mnemonic + " | " + course.name,
            }).appendTo("#course");
        });

    });*/

    $.getJSON(semesterEndpoint, function (data) {
        $.each(data, function (i, semester) {
            $("<option />", {
                val: semester.id,
                text: semester.season + " " + semester.year,
            }).appendTo("#semester");
        });

    });
});
// Clears all dropdown options & adds a disabled default option
function clearDropdown(id) {
    $(id).empty();
    $(id).html("<option value='' disabled selected>Select...</option>");
}