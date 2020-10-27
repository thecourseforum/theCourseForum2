import { validateForm } from "../common/form.js";

function submitForm(){
  var form = document.getElementById("bugform");
  var valid = validateForm(form);
  if (valid === true) {
    postToDiscord();
    // close form after submit
    $('#bugModal').modal('toggle');
    $('#confirmationModal').modal('toggle');
  }
}

function resetForm(){
  var form = document.getElementById("bugform");
  form.classList.remove('was-validated');
  var emailField = document.getElementById("emailField");
  emailField.value = "";
  var descriptionField = document.getElementById("descriptionField");
  descriptionField.value = "";
  $("#category1").prop("checked", false);
  $("#category2").prop("checked", false);
  $("#category3").prop("checked", false);
  $("#category4").prop("checked", false);
}

function postToDiscord(){
  var url = window.location.href;
  var email = $("#emailField").val();
  var description = $("#descriptionField").val();
  var categories = ""
  for(var i=1; i<=4; i++){
    var id = "#category" + i
    if($(id).is(':checked')){
      categories += "[" + $(id).val() + "]"
    }
  }
  var data = {
    "content": "Bug Found! \n**URL:** " + url +
                "\n**Description**: \n" + description +
                "\n**Categories: **"+ categories  +
                "\n**Email:** " + email
  }

  var discordURL = "https://discordapp.com/api/webhooks/767189878223142942/wwBQA0K4VQ0i94ku2os2tYIVpPbDtfeP1i6s5G3CBWSCI7R0t6PbhZxwgJ8Z2yYpyv-q"
  $.post( discordURL,
          data,
          function(){ });
}

document.getElementById("bugSubmitBtn").addEventListener("click", submitForm, false);
document.getElementById("bugFormOpen").addEventListener("click", resetForm, false);
