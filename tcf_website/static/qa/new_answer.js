jQuery(function($) {
    /* Fetch semester data for Answer dropdown */
    // Clear & disable sequenced dropdowns
    clearDropdown("#semester");

    const paramsArr = window.location.pathname.split("/");

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

// Below checks whether the user has already answered the question
$(document).ready(function() {
    $("#duplicate-answer").hide();

    $(document).on("click", "#answerQuestionBtn", function() {
        var questionId = $(this).data("id");
        $("#answerForm #2").val(questionId);
    });

    // Stop normal submit to check for duplicate answer with ajax request
    $("#answerForm").submit(function(e) {
        e.preventDefault();

        $.ajax({
            type: "POST",
            url: "/answers/check_duplicate/",
            data: $("#answerForm").serialize(),
            async: false,
            success: function(check) {
                if (check.duplicate) {
                    // Display error message for warning
                    $("#duplicate-answer").show();
                } else {
                    // Timeout button for 3 seconds so user can't spam button while form is submitting
                    $("#submitBtn").prop("disabled", true);
                    setTimeout(enableButton, 3000);
                    // Not a duplicate answer so proceed with normal form submission for new answer
                    document.getElementById("answerForm").submit();
                }
            }
        });
    });
});

// Re-enable button
function enableButton() {
    $("#submitBtn").prop("disabled", false);
}

// Clears all dropdown options & adds a disabled default option
function clearDropdown(id) {
    $(id).empty();
    $(id).html("<option value='' disabled selected>Select...</option>");
}
