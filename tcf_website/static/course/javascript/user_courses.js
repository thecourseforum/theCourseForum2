var numCourses = 0;

function unsaveCourse(course_id, instructor_id, id) {
    $.ajax({
        type: "GET",
        url: `/unsave_course/${course_id}/${instructor_id}`
    });

    document.getElementById(`course_${id}`).remove();

    numCourses--;
    if(numCourses==0){
        $("savedCoursesList").innerHTML = `
            <div class="card col p-5 text-center">
                <div class="card-body">
                    <h4 class="card-title">
                        No Saved Courses <i class="far fa-frown-open fa-fw"></i>
                    </h4>
                </div>
            </div>
            `;
    }
}

function editCourse(course_id, instructor_id, id){
    const notes = $(`#notesField${id}`).val();

    $.ajax({
        type: "GET",
        url: `/edit_course/${course_id}/${instructor_id}`,
        data: { notes: notes }
    });

    $(`#saveCourseModal${id}`).modal("toggle");
}

// Configure unsave and edit course buttons
var buttons = document.getElementsByClassName("save-btn");
numCourses = buttons.length;
for(var i=0; i<buttons.length; i++){
    const button = buttons[i];
    const saved_id = button.id.substring(13); // remove "saveCourseBtn"
    const course = document.getElementById(`course_id${saved_id}`).value;
    const instructor = document.getElementById(`instructor_id${saved_id}`).value;

    document.getElementById(`unsaveCourseBtn${saved_id}`).addEventListener("click", ()=>unsaveCourse(course, instructor, saved_id), false);
    document.getElementById(`saveCourseBtn${saved_id}`).addEventListener("click", ()=>editCourse(course, instructor, saved_id), false);
}

// source: https://docs.djangoproject.com/en/3.1/ref/csrf/
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

//Drag and Drop
$("#savedCoursesList").sortable();
$("#savedCoursesList").disableSelection();
$("#savedCoursesList").on( "sortupdate", function( event, ui ) {
    // save course order
    const moved = ui.item.context;
    const moved_id = moved.id.split("_")[1];
    const successor = $("#" + moved.id).prev()[0];
    const successor_id = successor.id.split("_")[1];
    const csrftoken = getCookie('csrftoken');

    console.log(moved_id);
    console.log(successor_id);
    $.ajaxSetup({
       headers: { "X-CSRFToken": csrftoken }
    });
    $.ajax({
        type: "POST",
        url: "/saved/reorder",
        data: {
           'to_move_id': moved_id,
           'successor_id':successor_id
        }
    });
} );
