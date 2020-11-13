function submitForm() {
    var fname = $("#inputFname").val();
    var lname = $("#inputLname").val();
    var email = $("#inputEmail").val();
    var title = $("#inputTitle").val();
    var message = $("#inputMessage").val();

    var data = {
        type: "feedback",
        content: "Feedback submitted" +
        "\n**Name:** " + fname + " " + lname +
        "\n**Email:** " + email +
        "\n**Title:** " + title +
        "\n**Message:** \n" + message
    };

    $.ajax({
        type: "GET",
        url: "/discord/",
        data: data
    });
}

document.getElementById("submitFeedbackBtn").addEventListener("submit", submitForm, false);
