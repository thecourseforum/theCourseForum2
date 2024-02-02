import { validateForm } from "../common/form.js";

function submitForm() {
    const form = document.getElementById("bugform");
    const valid = validateForm(form);
    if (valid === true) {
        postToDiscord();
        // close form after submit
        $("#bugModal").modal("toggle");
        $("#confirmationModal").modal("toggle");
    }
}

function resetForm() {
    const form = document.getElementById("bugform");
    form.classList.remove("was-validated");
    const emailField = document.getElementById("emailField");
    emailField.value = "";
    const descriptionField = document.getElementById("descriptionField");
    descriptionField.value = "";

    for (let i = 1; i <= 4; i++) {
        const id = "#category" + i;
        $(id).prop("checked", false);
    }
}

function postToDiscord() {
    const url = window.location.href;
    const email = $("#emailField").val();
    const description = $("#descriptionField").val();
    let categories = "";
    for (let i = 1; i <= 4; i++) {
        const id = "#category" + i;
        if ($(id).is(":checked")) {
            categories += "[" + $(id).val() + "]";
        }
    }
    const data = {
        type: "bug",
        content:
      "Bug Found! \n**URL:** " +
      url +
      "\n**Description**: \n" +
      description +
      "\n**Categories: **" +
      categories +
      "\n**Email:** " +
      email
    };

    $.ajax({
        type: "GET",
        url: "/discord/",
        data
    });
}

document
    .getElementById("bugSubmitBtn")
    .addEventListener("click", submitForm, false);
document
    .getElementById("bugFormOpen")
    .addEventListener("click", resetForm, false);
