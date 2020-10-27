import { validateForm } from "../common/form.js";

function submitForm(){
  var form = document.getElementById("bugform");
  var valid = validateForm(form);
  if (valid === true) {
    postToDiscord();
    // close form after submit
    $('#bugModal').modal('toggle');
  }
}

function resetForm(){
  var form = document.getElementById("bugform");
  form.classList.remove('was-validated');
  var emailField = document.getElementById("emailField");
  emailField.value = "";
  var descriptionField = document.getElementById("descriptionField");
  descriptionField.value = "";
}

function postToDiscord(){
  var url = window.location.href;
  var email = $("#emailField").val();
  var description = $("#descriptionField").val();
  var data = {
    "content": "Bug Found! \n**URL:** " + url + "\n**Description**: \n" + description + "\n**Email:** " + email
  }

  var discordURL = "https://discordapp.com/api/webhooks/767189878223142942/wwBQA0K4VQ0i94ku2os2tYIVpPbDtfeP1i6s5G3CBWSCI7R0t6PbhZxwgJ8Z2yYpyv-q"
  $.post( discordURL,
          data,
          function(){ });
}

document.getElementById("bugSubmitBtn").addEventListener("click", submitForm, false);
document.getElementById("bugFormOpen").addEventListener("click", resetForm, false);
