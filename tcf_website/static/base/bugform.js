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

        var content = "Bug Found! \n**URL:** " + url +
        "\n**Description:** \n" + description +
        "\n**Categories:**" + categories +
        "\n**Email:** " + email;
        postToDiscord("bug", content);

        content = "Bug Found! \n URL: " + url +
        "\nDescription: \n" + description +
        "\nCategories: " + categories +
        "\nEmail: " + email;
        sendEmail("Bug Report", content, "support@thecourseforum.com");

        content = "Thanks for reaching out! We received the following bug report from you:" +
        "\n\nDescription: \n" + description +
        "\nCategories:" + categories +
        "\n\nWe apologize for any inconveniences that this may have caused." +
        "Our team will be investigating the issue and will follow up with you shortly." +
        "\n\nBest, \ntheCourseForum Team";
        sendEmail("[theCourseForum] Thank you for your feedback!", content, email);
    }
}

const form = document.getElementById("bugform");
form.onsubmit = submit;

// Show confirmation modal on form submit
$("#bugform").submit(function(e) {
    $("#bugModal").modal("hide");
    $("#confirmationModal").modal("show");
    return false;
});
