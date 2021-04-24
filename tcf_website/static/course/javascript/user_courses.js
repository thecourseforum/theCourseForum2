function unsaveCourse(courseID, instructorID, id) {
    $.ajax({
        type: "GET",
        url: `/unsave_course/${courseID}/${instructorID}`
    });

    document.getElementById(`course${id}`).remove();

    // if no more courses left
    if ($(".course-card").length === 0) {
        document.getElementById("courseToolbar").remove();
        $("#savedCoursesList").html(`
            <div class="card col p-5 text-center">
                <div class="card-body">
                    <h4 class="card-title">
                        No Saved Courses <i class="far fa-frown-open fa-fw"></i>
                    </h4>
                </div>
            </div>
            `);
    }
}

function editCourse(courseID, instructorID, id) {
    const notes = $(`#notesField${id}`).val();

    $.ajax({
        type: "GET",
        url: `/save_course/${courseID}/${instructorID}/edit`,
        data: { notes: notes }
    });

    $(`#notes${id}`).text(notes);
}

// Configure unsave and edit course buttons
var buttons = document.getElementsByClassName("save-btn");
for (var i = 0; i < buttons.length; i++) {
    const button = buttons[i];
    const id = button.id.substring(13); // remove "saveCourseBtn" from string
    const course = $(`#courseID${id}`).val();
    const instructor = $(`#instructorID${id}`).val();

    document.getElementById(`unsaveCourseBtn${id}`).addEventListener("click", () => unsaveCourse(course, instructor, id), false);
    document.getElementById(`saveCourseBtn${id}`).addEventListener("click", () => editCourse(course, instructor, id), false);
}

// source: https://docs.djangoproject.com/en/3.1/ref/csrf/
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Drag and Drop
$("#savedCoursesList").sortable();
$("#savedCoursesList").disableSelection();

$("#savedCoursesList").on("sortstart", function(event, ui) {
    // highlight border when dragging
    const moved = ui.item.context;
    const movedID = moved.id.substring(6); // remove "course" from string
    $(`#card${movedID}`).addClass("dragging");
});

$("#savedCoursesList").on("sortstop", function(event, ui) {
    // remove border highlight
    const moved = ui.item.context;
    const movedID = moved.id.substring(6); // remove "course" from string
    $(`#card${movedID}`).removeClass("dragging");
});

$("#savedCoursesList").on("sortupdate", function(event, ui) {
    // save course order
    const moved = ui.item.context;
    const movedID = moved.id.substring(6); // remove "course" from string
    const successor = $(`#${moved.id}`).prev("li")[0];
    const csrftoken = getCookie("csrftoken");
    var data;
    try {
        const successorID = successor.id.substring(6);
        data = {
            to_move_id: movedID,
            successor_id: successorID
        };
    } catch (error) {
        // successor ID is undefined, move to beginning of list
        data = {
            to_move_id: movedID
        };
    }

    $.ajaxSetup({
        headers: { "X-CSRFToken": csrftoken }
    });

    $.ajax({
        type: "POST",
        url: "/saved/reorder",
        data: data
    });

    // clear sort buttons
    $("#number-sort-btn").removeClass("active");
    $("#rating-sort-btn").removeClass("active");
    $("#diff-sort-btn").removeClass("active");
    $("#gpa-sort-btn").removeClass("active");
    $("#number-sort-btn").html("Course ID");
    $("#rating-sort-btn").html("Rating");
    $("#diff-sort-btn").html("Difficulty");
    $("#gpa-sort-btn").html("GPA");
});
