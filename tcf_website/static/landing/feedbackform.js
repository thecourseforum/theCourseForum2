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

        var content = "Feedback submitted" +
        "\n**Name:** " + fname + " " + lname +
        "\n**Email:** " + email +
        "\n**Title:** " + title +
        "\n**Message:** \n" + message;

        postToDiscord("feedback", content);

        content = "Feedback submitted" +
        "\nName: " + fname + " " + lname +
        "\nEmail: " + email +
        "\nTitle: " + title +
        "\nMessage: \n" + message;
        sendEmail("[Feedback]" + title, content, "support@thecourseforum.com");

        content = "Hi " + fname + ", " +
        "\n\nThanks for reaching out! We received the following feedback from you:" +
        "\nTitle: " + title +
        "\nMessage: \n" + message +
        "\n\nWe greatly appreciate you taking the time to help us improve tCF!" +
        "A team member will be following up with you shortly if neccesary." +
        "\n\nBest, \ntheCourseForum Team";
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
