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
                body: formData
            })
                .then(resp => {
                    if (resp.ok) {
                        location.reload();
                    } else {
                        submitButton.disabled = false;
                        console.error("There was an error");
                    }
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

            // add the courseId into the url's query string
            fetch_url += courseId;

            fetch(fetch_url, {
                method: "GET"
            })
                .then(resp => resp.json())
                .then(data => {
                    if (data.mode === "edit") {
                        schedule_edit_submit(selectedSchedule, next_modal_id, data);
                    } else {
                        course_add_submit(selectedSchedule, next_modal_id, data);
                    }
                })
                .catch(error => {
                    console.error("Error:", error);
                    alert("Something went wrong");
                });
        });
    }

    // add the general modal listeners
    generalModalListeners();
}

function schedule_edit_submit(selectedSchedule, next_modal_id, data) {
    // this function is for handling the modal when the content is for editting a schedule

    // set hidden field for on the edit_schedule_modal form
    document.getElementById("schedule_id_input").value = selectedSchedule;
    section_form = document.getElementById("select_section_form");
}

function course_add_submit(selectedSchedule, next_modal_id, data) {
    // this function is for handling the modal when the content is for adding a course

    // set hidden field for on the add_course_modal form
    document.getElementById("schedule_id_input").value = selectedSchedule;
    section_form = document.getElementById("select_section_form");

    // iterate over all returned instructors and create the html cards for them
    // TODO: check to see if something is returned and that it's not null
    for (const [insId, insInfo] of Object.entries(data)) {
        // create the card that will contain all info for a given instructor
        var instructorDiv = document.createElement("div");
        instructorDiv.className = "modal_instructor_card";
        instructorDiv.id = "modal_instructor_card" + insId;

        // create the title of the card as the instructor's name
        var instructorName = document.createElement("h6");
        instructorName.textContent = insInfo.name;
        instructorDiv.appendChild(instructorName);

        // create a hidden input to store the instructor's id
        var instructorId = document.createElement("input");
        instructorId.type = "hidden";
        instructorId.value = insId;

        var sectionsList = document.createElement("ul");

        insInfo.sections.forEach(encoded_section => {
            var decoded_section = encoded_section.split(" /% ");
            var section_id = decoded_section[0];
            var section_num = decoded_section[1];
            var section_time = decoded_section[2].slice(0, -1);

            var li = document.createElement("li");
            var lab = document.createElement("label");
            lab.textContent = section_time;
            var input = document.createElement("input");
            input.type = "radio";
            input.name = "selected_course";
            input.value = `{"instructor": ${insId}, "section": ${section_id}, "section_time":"${section_time}"}`;

            lab.appendChild(input);
            li.appendChild(lab);
            sectionsList.appendChild(li);
        });

        instructorDiv.appendChild(sectionsList);
        section_form.appendChild(instructorDiv);
    }

    // close the select schedule modal and then open the next modal
    $("#selectScheduleModal").modal("hide");
    setTimeout(function() {
        $(next_modal_id).modal("show");
    }, 400);
}
