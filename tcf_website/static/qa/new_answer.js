function populateDropdown(dropdownID) {
    /* Fetch semester data for Answer dropdown */
    // Clear & disable sequenced dropdowns
    clearDropdown(dropdownID);
    const selectedSemID = parseInt(dropdownID.split("-")[1]);

    const paramsArr = window.location.pathname.split("/");

    // Fetch all semester data from API
    const course = paramsArr[2];
    const instrID = paramsArr[3];
    const semEndpoint = `/api/semesters/?course=${course}&instructor=${instrID}`;
    $.getJSON(semEndpoint, function(data) {
    // Generate option tags
        if (data.length === 0) {
            $("#ask-question-button").addClass("disabled");
            $(".answerQuestionBtn").addClass("disabled");
        } else {
            $.each(data, function(i, semester) {
                $("<option />", {
                    val: semester.id,
                    text: semester.season + " " + semester.year
                }).appendTo(dropdownID);

                if (selectedSemID === semester.id) {
                    $(dropdownID).val(semester.id);
                }
            });
        }
        return this;
    }).done(function() {
    // Enable semester selector
        $(dropdownID).prop("disabled", false);
    });
}

jQuery(function($) {
    // Get all dropdown ids in the semester dropdown class for edit answer forms, clear and populate each
    const ids = $(".semester-dropdown")
        .map(function(_, x) {
            return "#".concat(x.id);
        })
        .get();
    ids.forEach((item) => populateDropdown(item));
});

// Below checks whether the user has already answered the question
$(document).ready(function() {
    $("#duplicate-answer").hide();

    $(document).on("click", "#answerQuestionBtn", function() {
        const questionId = $(this).data("id");
        $("#answerForm #questionInput").val(questionId);
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
