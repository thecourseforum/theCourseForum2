// form validation
// parameter: eg. var form = document.getElementById("bugform");
function validateForm(form) {
    var valid = form.checkValidity();
    if (valid === false) {
        event.preventDefault();
        event.stopPropagation();
    }
    form.classList.add("was-validated");

    var email = $("#inputEmail").val();
    if (email.endsWith("@virginia.edu", 3)) {
        valid = false;
    }
    return valid;
}

export { validateForm };
