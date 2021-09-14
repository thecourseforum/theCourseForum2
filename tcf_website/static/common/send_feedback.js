function postToDiscord(type, message) {
    const data = {
        type: type,
        content: message
    };

    const csrftoken = getCookie("csrftoken");

    $.ajax({
        type: "POST",
        headers: { "X-CSRFToken": csrftoken },
        url: "/feedback/discord",
        data: data
    });
}

function sendEmail(subject, message, recipient) {
    const data = {
        subject: subject,
        content: message,
        recipient: recipient
    };

    const csrftoken = getCookie("csrftoken");

    $.ajax({
        type: "POST",
        headers: { "X-CSRFToken": csrftoken },
        url: "/feedback/email",
        data: data
    });
}

export { postToDiscord, sendEmail };
