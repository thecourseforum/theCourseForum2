function submitForm(){
  var form = document.getElementById("bugform");
  if (form.checkValidity() === false) {
    event.preventDefault();
    event.stopPropagation();
  }else{
    postToDiscord();
    $('#bugModal').modal('toggle');
  }
  form.classList.add('was-validated');
}

function postToDiscord(){
  var url = $("#urlField").val();
  var email = $("#emailField").val();
  var description = $("#descriptionField").val();
  var data = {
    "content": "Bug Found! \n**URL:** " + url + "\n**Description**: \n" + description + "\n**Email:** " + email
  }

  var discordURL = "https://discordapp.com/api/webhooks/767189878223142942/wwBQA0K4VQ0i94ku2os2tYIVpPbDtfeP1i6s5G3CBWSCI7R0t6PbhZxwgJ8Z2yYpyv-q"
  $.post( discordURL,
          data,
          function(){ console.log("posted to discord") });
}

function setUrlField() {
  var urlField = document.getElementById("urlField");
  urlField.value = window.location.href;
}
