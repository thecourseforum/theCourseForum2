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

function sendEmail(subject, message, recipient) {
    var data = {
        subject: subject,
        content: message,
        recipient: recipient
    };

    $.ajax({
        type: "GET",
        url: "/feedback/email",
        data: data
    });
}

export { postToDiscord, sendEmail };
