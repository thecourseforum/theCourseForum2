var num_courses = 0;

function unsaveCourse(course_id, instructor_id) {
    $.ajax({
        type: "GET",
        url: `/unsave_course/${course_id}/${instructor_id}`
    });

    document.getElementById(`course_${course_id}_${instructor_id}`).remove();

    num_courses--;
    if(num_courses==0){
        document.getElementById("saved_courses_block").innerHTML = `
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

var buttons = document.getElementsByClassName("unsave_btn");
for(var i=0; i<buttons.length; i++){
    const x = buttons[i].id.split("_");
    const course = x[1];
    const instructor = x[2];

    num_courses++;
    buttons[i].addEventListener("click", ()=>unsaveCourse(course, instructor), false);
}
