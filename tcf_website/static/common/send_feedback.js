function postToDiscord(type, content) {
    const data = {
        type: type,
        content: content
    };

    const csrftoken = getCookie("csrftoken");

    $.ajax({
        type: "POST",
        headers: { "X-CSRFToken": csrftoken },
        url: "/feedback/discord",
        data: data
    });
}

function sendEmail(type, content) {
    const data = {
        type: type,
        content: content
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
