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
    console.log(buttons[i]);
    var x = buttons[i].id.split("_");
    var course_id = x[1];
    var instructor_id = x[2];

    num_courses++;
    document.addEventListener("click", ()=>unsaveCourse(course_id, instructor_id), false);
}
