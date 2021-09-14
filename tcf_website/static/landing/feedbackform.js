import { validateForm, validateEmail } from "../common/form.js";
import { postToDiscord, sendEmail } from "../common/send_feedback.js";

function submit(event) {
    const form = document.getElementById("feedbackform");
    if (validateForm(form) === true) {
        const fname = $("#inputFname").val();
        const lname = $("#inputLname").val();
        const email = $("#inputEmail").val();
        const title = $("#inputTitle").val();
        const message = $("#inputMessage").val();

        // Post to DIscord
        const discordContent = `
        Feedback submitted
        **Name:** ${fname} ${lname}
        **Email:** ${email}
        **Title:** ${title}
        **Message:** ${message}
        `;
        postToDiscord("feedback", discordContent);

        // Send email
        if(validateEmail(email) === true){
            const subject = "[theCourseForum] Thank you for your feedback!";
            const emailContent = `
            Hi ${fname},
            Thanks for reaching out! We received the following feedback from you:
            Title: ${title}
            Message: ${message}
            We greatly appreciate you taking the time to help us improve tCF!
            A team member will be following up with you shortly if neccesary.
            Best,
            theCourseForum Team
            `;
            sendEmail(subject, emailContent, email);
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
