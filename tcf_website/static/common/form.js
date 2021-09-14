// form validation
// parameter: eg. var form = document.getElementById("bugform");
function validateForm(form) {
    var valid = form.checkValidity();
    if (valid === false) {
        event.preventDefault();
        event.stopPropagation();
    }
    form.classList.add("was-validated");

    return valid;
}

function validateEmail(email) {
    const re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

export { validateForm, validateEmail };
