import { validateForm } from "../common/form.js";
import { postToDiscord, sendEmail } from "../common/send_feedback.js";

function submit(event) {
    var form = document.getElementById("feedbackform");
    var valid = validateForm(form);
    if (valid === true) {
        var fname = $("#inputFname").val();
        var lname = $("#inputLname").val();
        var email = $("#inputEmail").val();
        var title = $("#inputTitle").val();
        var message = $("#inputMessage").val();

        var content = `
        Feedback submitted
        **Name:** ${fname} ${lname}
        **Email:** ${email}
        **Title:** ${title}
        **Message:** ${message}
        `;
        postToDiscord("feedback", content);

        content = `
        Feedback submitted
        Name: ${fname} ${lname}
        Email: ${email}
        Title: ${title}
        Message: ${message}
        `;
        sendEmail("[Feedback]" + title, content, "support@thecourseforum.com");

        content = `
        Hi ${fname},
        Thanks for reaching out! We received the following feedback from you:
        Title: ${title}
        Message: ${message}

        We greatly appreciate you taking the time to help us improve tCF!
        A team member will be following up with you shortly if neccesary.
        
        Best,
        theCourseForum Team
        `;
        sendEmail("[theCourseForum] Thank you for your feedback!", content, email);
    }
}

const form = document.getElementById("feedbackform");
form.onsubmit = submit;

// Show confirmation modal on form submit
$("#feedbackform").submit(function(e) {
    $("#confirmationModal").modal("show");
    return false;
});
