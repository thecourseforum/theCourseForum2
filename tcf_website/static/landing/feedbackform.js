import { validateForm } from "../common/form.js";
import { postToDiscord, sendEmail } from "../common/send_feedback.js";

function submit(event) {
    const form = document.getElementById("feedbackform");
    if (validateForm(form) === true) {
        const data = new FormData(form);
        const content = Object.fromEntries(data.entries());
        const type = "feedback";

        postToDiscord(type, content);
        if (content.email !== "") {
            sendEmail(type, content);
        }
    }
}

const form = document.getElementById("feedbackform");
form.onsubmit = submit;

// Show confirmation modal on form submit
$("#feedbackform").submit(function(e) {
    $("#confirmationModal").modal("show");
    return false;
});
