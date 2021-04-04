var numCourses = 0;

function unsaveCourse(course_id, instructor_id) {
    $.ajax({
        type: "GET",
        url: `/unsave_course/${course_id}/${instructor_id}`
    });

    document.getElementById(`course_${course_id}_${instructor_id}`).remove();

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

// Configure unsave course buttons
var buttons = document.getElementsByClassName("unsave-btn");
for(var i=0; i<buttons.length; i++){
    const button = buttons[i];
    const x = button.id.split("_");
    const course = x[1];
    const instructor = x[2];

    numCourses++;
    button.addEventListener("click", ()=>unsaveCourse(course, instructor), false);
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
    const moved_id = moved.id.split("_")[3];
    const successor = $("#" + moved.id).next()[0];
    const successor_id = successor.id.split("_")[3];
    const csrftoken = getCookie('csrftoken');

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
