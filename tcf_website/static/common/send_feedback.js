function postToDiscord(type, content) {
    const data = {
        type: type,
        content: JSON.stringify(content)
    };

    $.ajax({
        type: "POST",
        headers: { "X-CSRFToken": content.csrfmiddlewaretoken },
        url: "/feedback/discord",
        data: data
    });
}

function sendEmail(type, content) {
    const data = {
        type: type,
        content: JSON.stringify(content)
    };

    $.ajax({
        type: "POST",
        headers: { "X-CSRFToken": content.csrfmiddlewaretoken },
        url: "/feedback/email",
        data: data
    });
}

export { postToDiscord, sendEmail };
