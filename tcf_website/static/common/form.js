// form validation
// parameter: eg. var form = document.getElementById("bugform");
function validateForm(form, email) {
    var valid = form.checkValidity();
    if (valid === false || email.endsWith("@virginia.edu") === false) {
        event.preventDefault();
        event.stopPropagation();
    }
    form.classList.add("was-validated");
    return valid;
}

export { validateForm };
