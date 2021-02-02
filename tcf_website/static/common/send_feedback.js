function postToDiscord(type, message) {
    var data = {
        type: "bug",
        content: message
    };

    $.ajax({
        type: "GET",
        url: "/discord/",
        data: data
    });
}

function sendEmail(email, subject, message) {
    var data = {
        email: email,
        subject: subject,
        content: message
    };

    $.ajax({
        type: "GET",
        url: "/email/",
        data: data
    });
}

export { postToDiscord, sendEmail };
