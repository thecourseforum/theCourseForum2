// Populate the dropdown options for the new question form
// Executed when DOM is ready
jQuery(function ($) {
    /* Fetch subject(subdepartment) data initially */
    // Clear & disable sequenced dropdowns
    clearDropdown("#school");
    clearDropdown("#subject");
    clearDropdown("#course");
    clearDropdown("#instructor");

    // If coming from the sidebar, params.length = 0
    // If coming from a course professor page, params.length > 0
    const params = window.location.search;
    let schoolID, subdeptID, courseID, instructorID;
    if (params.length > 0) {
        const paramsArr = params.split("&");
        schoolID = parseInt(paramsArr[0].replace("?school_id=", ""));
        subdeptID = parseInt(paramsArr[1].replace("?subdept_id=", ""));
        courseID = parseInt(paramsArr[2].replace("course_id=", ""));
        instructorID = parseInt(paramsArr[3].replace("instr_id=", ""));
    }

    const schoolEndpoint = "/api/schools/";
    const departmentEndpoint = "/api/departments/";
    const subdeptEndpoint = "/api/subdepartments/";

    /* Fetch all data on school select */
    $.getJSON(schoolEndpoint, function (data) {

        // Generate option tags
        $.each(data, function (i, school) {
            $("<option />", {
                val: school.id,
                text: school.name,
                // Check for autofill
                selected: school.id === schoolID
            }).appendTo("#school");
            // Trigger change on autofill
            if (school.id === schoolID) {
                $("#school").trigger("change");
            }
        });

    }).done(function () {
        $("#school").prop("disabled", false);
        $("#subject").prop("disabled", true);
        $("#course").prop("disabled", true);
        $("#instructor").prop("disabled", true);
    }
    );

    /* Fetch data on subject select belonging to the school */
    $("#school").change(function () {
        clearDropdown("#subject");
        clearDropdown("#course");
        clearDropdown("#instructor");

        const departmentSet = new Set();
        $.getJSON(departmentEndpoint, function (data) {
            $.each(data, function (i, department) {
                if (department.school.id === parseInt($("#school").val())) {
                    departmentSet.add(department.id);
                }
            })
        }).done(function () {
            $.getJSON(subdeptEndpoint, function (data) {
                // Sort departments alphabetically by mnemonic
                data.sort(function (a, b) {
                    return a.mnemonic.localeCompare(b.mnemonic);
                });

                // Generate option tags
                $.each(data, function (i, subdept) {
                    if (departmentSet.has(subdept.department)) {
                        $("<option />", {
                            val: subdept.id,
                            text: subdept.mnemonic + " | " + subdept.name,
                            // Check for autofill
                            selected: subdept.id === subdeptID
                        }).appendTo("#subject");

                        // Trigger change on autofill
                        if (subdept.id === subdeptID) {
                            $("#subject").trigger("change");
                        }
                    }
                });
                return this;
            })
        }).done(function () { // Second callback
            // Enable subject selector, disable the following
            $("#subject").prop("disabled", false);
            $("#course").prop("disabled", true);
            $("#instructor").prop("disabled", true);
        });
    });

    /* Fetch course data on subject select */
    $("#subject").change(function () {
        // Clear & disable sequenced dropdowns
        clearDropdown("#course");
        clearDropdown("#instructor");

        // Fetch course data from API, based on selected subdepartment
        const subdeptID = $("#subject").val();
        const pageSize = "1000";
        const courseEndpoint = `/api/courses/?subdepartment=${subdeptID}
                              &page_size=${pageSize}&recent`;
        $.getJSON(courseEndpoint, function (data) {
            // Generate option tags
            $.each(data.results, function (i, course) {
                $("<option />", {
                    val: course.id,
                    text: course.number + " | " + course.title,
                    // Check for autofill
                    selected: course.id === courseID
                }).appendTo("#course");
                // Trigger change on autofill
                if (course.id === courseID) {
                    $("#course").trigger("change");
                }
            });
            return this;
        })
            .done(function () {
                // Enable course selector, disable the following
                $("#course").prop("disabled", false);
                $("#instructor").prop("disabled", true);
            });
    });

    /* Fetch instructor data on course select */
    $("#course").change(function () {
        // Clear & disable sequenced dropdowns
        clearDropdown("#instructor");

        // Fetch instructor data from API, based on selected course
        const course = $("#course").val();
        const pageSize = "1000";
        const instrEndpoint = `/api/instructors/?course=${course}` +
            `&page_size=${pageSize}`;
        $.getJSON(instrEndpoint, function (data) {
            clearDropdown("#instructor"); // Empty dropdown

            // Generate option tags
            $.each(data.results, function (i, instr) {
                $("<option />", {
                    val: instr.id,
                    text: instr.last_name + ", " + instr.first_name,
                    // Check for autofill
                    selected: instr.id === instructorID
                }).appendTo("#instructor");
                // Trigger change on autofill
                if (instr.id === instructorID) {
                    $("#instructor").trigger("change");
                }
            });
            return this;
        })
            .done(function () {
                // Enable instructor selector, disable the following
                $("#instructor").prop("disabled", false);
            });
    });
});

// Clears all dropdown options & adds a disabled default option
function clearDropdown(id) {
    $(id).empty();
    $(id).html("<option value='' disabled selected>Select...</option>");
}
