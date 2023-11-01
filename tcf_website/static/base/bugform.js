import { validateForm } from "../common/form.js";

function submitForm() {
    var form = document.getElementById("bugform");
    var email = $("emailField").val();
    var description = $("#descriptionField").val();
    var valid = validateForm(form, email);
    if (valid === true) {
        postToDiscord(email, description);
        // close form after submit
        $("#bugModal").modal("toggle");
        $("#confirmationModal").modal("toggle");
    }
}

function resetForm() {
    var form = document.getElementById("bugform");
    var emailField = document.getElementById("emailField");
    var descriptionField = document.getElementById("descriptionField");
    form.classList.remove("was-validated");
    emailField.value = "";
    descriptionField.value = "";

    for (var i = 1; i <= 4; i++) {
        var id = "#category" + i;
        $(id).prop("checked", false);
    }
}

function postToDiscord(email, description) {
    var url = window.location.href;
    var categories = "";
    for (var i = 1; i <= 4; i++) {
        var id = "#category" + i;
        if ($(id).is(":checked")) {
            categories += "[" + $(id).val() + "]";
        }
    }
    var data = {
        type: "bug",
        content: "Bug Found! \n**URL:** " + url +
        "\n**Description**: \n" + description +
        "\n**Categories: **" + categories +
        "\n**Email:** " + email
    };

    $.ajax({
        type: "GET",
        url: "/discord/",
        data: data
    });
}

document.getElementById("bugSubmitBtn").addEventListener("click", submitForm, false);
document.getElementById("bugFormOpen").addEventListener("click", resetForm, false);
