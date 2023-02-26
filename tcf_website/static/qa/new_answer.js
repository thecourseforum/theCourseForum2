jQuery(function($) {
    console.log("hi world");

    /* Fetch semester data for Answer dropdown */
    // Clear & disable sequenced dropdowns
    clearDropdown("#semester");

    const paramsArr = window.location.pathname.split("/");
    console.log(paramsArr);

    // Fetch all semester data from API
    var course = paramsArr[2];
    var instrID = paramsArr[3];
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

// Clears all dropdown options & adds a disabled default option
function clearDropdown(id) {
    $(id).empty();
    $(id).html("<option value='' disabled selected>Select...</option>");
}
