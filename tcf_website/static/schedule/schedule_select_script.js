/* eslint-disable */
window.modalFunctions = function(courseIdParam, modeParam, modalSubmitUrlParam) {
    var modalSubmitUrl = "";
    var nextModalId = "";

    if( modeParam == "add_course"){
        modalSubmitUrl = modalSubmitUrlParam;
        nextModalId = '#addCourseModal';
    } else if( modeParam == "edit_schedule") {
        modalSubmitUrl = modalSubmitUrlParam;
        nextModalId = '#editScheduleModal';
    } else {
        console.error("invalid or missing mode");
    }

    const courseId = courseIdParam;
    window.attachEventListenersToModalContent(modalSubmitUrl, nextModalId, courseId);
    console.log(courseId);
    if(courseId) {
        document.getElementById("select_schedule_form").setAttribute("data-course-id", courseId);
    }
}


window.enableSubmit = function() {
var submitButton = document.getElementById('schedule_select_btn');
submitButton.disabled = false;
}

window.attachEventListenersToModalContent = function(fetch_url, next_modal_id, courseIdParam) {
    // the fetch_url is the endpoint for loading the content into the modal

    var form = document.getElementById("select_schedule_form");
    if ( !form) {
    console.error("ERROR: missing form");
    return;
    }

    form.addEventListener("submit", function(event) {
    event.preventDefault();
    document.getElementById("schedule_select_btn").disabled = true; // prevent a double submission

    // get the related data from the form
    var selectedSchedule = form.querySelector('input[type="radio"][name="selected_schedules"]:checked').value;
    var courseId = courseIdParam;

    // prepare the request body
    requestBody = {};
    requestBody['schedule_id'] = selectedSchedule;
    
    if (fetch_url == '/schedule/modal/editor') {
        // if the fetch URL is for loading the editor, proceed
    }
    else {
        // else the other option is for loading the course sections
        requestBody['course_id'] = courseId;
    }

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
            $("#second-modal-body").html(html);
            
            // close the select schedule modal and then open the next modal
            $("#selectScheduleModal").modal("hide");
            setTimeout(function() {
                // show the modal and then dispatch an event to the modal to
                // let it know when to attach the submit event listener
                $(next_modal_id).modal("show");
                var modal = document.getElementById(next_modal_id.substring(1));
                var modalEvent = new Event("modalLoaded");
                modal.dispatchEvent(modalEvent);
            }, 400);

        })
        .catch(error => {
            console.error("Error:", error);
            alert("Something went wrong");
        });
    });

}
