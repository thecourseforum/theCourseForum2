import { validateForm } from "../common/form.js";
import { postToDiscord, sendEmail } from "../common/send_feedback.js";

function submit(event) {
    const form = document.getElementById("bugform");
    const valid = validateForm(form);
    if (valid === true) {
        const url = window.location.href;
        const email = $("#emailField").val();
        const description = $("#descriptionField").val();
        let categories = "";
        for (let i = 1; i <= 4; i++) {
            const id = "#category" + i;
            if ($(id).is(":checked")) {
                categories += "[" + $(id).val() + "]";
            }
        }

        const discordContent = `
        Bug Found!
        **URL:** ${url}
        **Categories:** ${categories}
        **Email:** ${email}
        **Description:** ${description}
        `;
        postToDiscord("bug", discordContent);

        const subject = "[theCourseForum] Thank you for your feedback!";
        const emailContent = `
        Thanks for reaching out! We received the following bug report from you:
        Description: ${description}
        Categories: ${categories}
        We apologize for any inconveniences that this may have caused.
        Our team will be investigating the issue and will follow up with you shortly.
        Best,
        theCourseForum Team
        `;
        sendEmail(subject, emailContent, email);

        resetForm();
    }
}

function resetForm() {
    $("#bugform").removeClass("was-validated");
    $("#emailField").val("");
    $("#descriptionField").val("");

    for (let i = 1; i <= 4; i++) {
        const id = "#category" + i;
        $(id).prop("checked", false);
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
