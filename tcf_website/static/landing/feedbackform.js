function submit(event) {
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

const form = document.getElementById("feedbackform");
form.onsubmit = submit;
