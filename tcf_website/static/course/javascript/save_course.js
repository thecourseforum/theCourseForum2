
function saveCourse() {
    const notes = $(`#notesField${courseID}`).val();

    $.ajax({
        type: "GET",
        url: `/save_course/${courseID}/${instructorID}`,
        data: { notes: notes }
    });

    document.getElementById("saveCourseBtn").style = "display: none!important;";
    document.getElementById("unsaveCourseBtn").style = "display: auto;";
}

function unsaveCourse() {
    $.ajax({
        type: "GET",
        url: `/unsave_course/${courseID}/${instructorID}`
    });

    document.getElementById("saveCourseBtn").style = "display: auto;";
    document.getElementById("unsaveCourseBtn").style = "display: none!important;";
}

document.getElementById(`saveCourseBtn${courseID}`).addEventListener("click", saveCourse, false);
document.getElementById("unsaveCourseBtn").addEventListener("click", unsaveCourse, false);
