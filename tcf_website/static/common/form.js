// form validation
// parameter: eg. var form = document.getElementById("bugform");
function validateForm(form) {
  const valid = form.checkValidity();
  if (valid === false) {
    event.preventDefault();
    event.stopPropagation();
  }
  form.classList.add("was-validated");

  return valid;
}

export { validateForm };
