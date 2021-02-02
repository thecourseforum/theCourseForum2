function postToDiscord(type, message) {
    var data = {
        type: type,
        content: message
    };

    $.ajax({
        type: "GET",
        url: "/feedback/discord",
        data: data
    });
}

function sendEmail(subject, message, recipients) {
    console.log(recipients)
    var data = {
        subject: subject,
        content: message,
        recipients: recipients
    };

    $.ajax({
        type: "GET",
        url: "/feedback/email",
        data: data
    });
}

export { postToDiscord, sendEmail };
