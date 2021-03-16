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
