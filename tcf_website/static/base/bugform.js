import { validateForm } from "../common/form.js";
import { postToDiscord, sendEmail } from "../common/send_feedback.js";

function submit(event) {
    const form = document.getElementById("bugform");
    if (validateForm(form) === true) {
        // Extract fields
        const data = new FormData(form);
        const content = Object.fromEntries(data.entries());
        content.categories = data.getAll("categories"); // handle checkboxes
        content.url = window.location.href; // get current url
        const type = "bug";

        postToDiscord(type, content);
        if (content.email !== "") {
            sendEmail(type, content);
        }
        resetForm();
    }
}

function resetForm() {
    $("#bugform").removeClass("was-validated");
    $("#inputEmail").val("");
    $("#inputDescription").val("");

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
