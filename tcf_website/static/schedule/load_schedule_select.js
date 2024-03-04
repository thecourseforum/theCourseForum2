/* eslint-disable */

function loadModal(modalFetchUrl, modalSubmitUrl, nextModalId, courseId) {
    // this AJAX request gets the html data to load into the modal
    // - modalFetchUrl : this parameter is the intial url request into the modal
    // - modalSubmitUrl : this parameter is the url that's used for to get the next modal
    $.ajax({
        url: modalFetchUrl,
        success: function(data) {
            $("#modal-body").html(data); // Insert the response data into the modal
            document.getElementById("select_schedule_form").setAttribute("data-course-id", courseId);
            $("#selectScheduleModal").modal("show"); // Show the modal
            attachEventListenersToModalContent(modalSubmitUrl, nextModalId);
        }
    });
}

function generalModalListeners() {
    // this function is for the general functionality of the modal
    // for example: preventing double submission, enforcing one selecton

    var sectionForm = document.getElementById("select_section_form");
    if (sectionForm) {
        // this will prevent a submit without a selection
        var submitButton = document.getElementById("section_select_btn");

        // Function to check the inputs and enable the button if criteria is met
        function updateButtonState() {
            var inputs = sectionForm.querySelectorAll('input[type="radio"]');
            var isAnyInputFilled = Array.from(inputs).some(radio => radio.checked);
            submitButton.disabled = !isAnyInputFilled;
        }

        // Event listener for changes in the form
        sectionForm.addEventListener("change", updateButtonState);

        // Initial check in case the form is pre-filled
        updateButtonState();

        // this will use a listener to send the form data to the view
        sectionForm.addEventListener("submit", function(event) {
            event.preventDefault();
            // prevent double submission
            submitButton.disabled = true;
            
            var formData = new FormData(this);
            fetch(this.action, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: formData
            })
                .then(resp => {
                    if (resp.ok) {
                        location.reload();
                    }
                })
                .catch(error => {
                    submitButton.disabled = false;
                    console.error("Error:", error);
                    alert("Something went wrong");
                });
        });
    }
}

function attachEventListenersToModalContent(fetch_url, next_modal_id) {
    // the fetch_url is the endpoint for loading the content into the modal

    var form = document.getElementById("select_schedule_form");
    if (form) {
        form.addEventListener("submit", function(event) {
            event.preventDefault();
            document.getElementById("schedule_select_btn").disabled = true; // prevent a double submission

            var selectedSchedule = form.querySelector('input[type="radio"][name="selected_schedules"]:checked').value;
            var courseId = form.getAttribute("data-course-id");

            requestBody = {};
            requestBody['course_id'] = courseId;
            requestBody['schedule_id'] = selectedSchedule;

            fetch(fetch_url, {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json',
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: JSON.stringify(requestBody)
            })
                .then(resp => resp.text())
                .then(html => {
                    // insert the returned HTML and update hidden schedule ID
                    $("#schedule_and_sections").html(html);
                    document.getElementById("schedule_id_input").value = selectedSchedule;

                    // close the select schedule modal and then open the next modal
                    $("#selectScheduleModal").modal("hide");
                    setTimeout(function() {
                        $(next_modal_id).modal("show");
                    }, 400);

                    // add the general modal listeners
                    generalModalListeners();
                })
                .catch(error => {
                    console.error("Error:", error);
                    alert("Something went wrong");
                });
        });

    }

}
