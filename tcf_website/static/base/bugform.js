import { validateForm } from "../common/form.js";
import { postToDiscord, sendEmail } from "../common/send_feedback.js";

function submit(event) {
    var form = document.getElementById("bugform");
    var valid = validateForm(form);
    if (valid === true) {
        var url = window.location.href;
        var email = $("#emailField").val();
        var description = $("#descriptionField").val();
        var categories = "";
        for (var i = 1; i <= 4; i++) {
            var id = "#category" + i;
            if ($(id).is(":checked")) {
                categories += "[" + $(id).val() + "]";
            }
        }

        var message = "Bug Found! \n**URL:** " + url +
        "\n**Description**: \n" + description +
        "\n**Categories: **" + categories

        var content = message + "\n**Email:** " + email

        console.log(message);
        postToDiscord("bug", content);
        sendEmail(email, "Bug Report", message);

        // close form after submit
        $("#bugModal").modal("toggle");
        $("#confirmationModal").modal("toggle");
    }
}

const form = document.getElementById("bugform");
form.onsubmit = submit;
