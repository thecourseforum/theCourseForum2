function unsaveCourse(course_id, instructor_id) {
    $.ajax({
        type: "GET",
        url: `/unsave_course/${course_id}/${instructor_id}`
    });

    document.getElementById(`course_${saved.course_id}_${saved.instructor_id}`).remove();
}

var buttons = document.getElementsByClassName("btn");
for(var button in buttons){
    var x = button.id.split("_");
    var course_id = x[1];
    var instructor_id = x[2];

    document.addEventListener("click", ()=>unsaveCourse(course_id, instructor_id), false);
}
