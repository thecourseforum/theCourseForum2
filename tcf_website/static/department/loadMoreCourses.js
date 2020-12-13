async function loadPage(subdepartmentId, url) {
    if (url === null) {
        hideSpinner(subdepartmentId);
        return;
    };
    const courses = await fetch(url).then(res => res.json());
    if (courses.detail === "Invalid page.") {
        hideSpinner(subdepartmentId);
    } else {
        const element = document.getElementById(`courses-sd-${subdepartmentId}`);
        const htmlArray = [];
        courses.results.forEach((course) => {
            const html = generateCourseCardHTML(course);
            htmlArray.push(html);
        });
        element.insertAdjacentHTML("beforeend", htmlArray.join(""));
        loadPage(subdepartmentId, courses.next);
    }
}

function generateCourseCardHTML(course) {
    const rating = emdashOrTwoDecimals(course.average_rating);
    const difficulty = emdashOrTwoDecimals(course.average_difficulty);
    const gpa = emdashOrTwoDecimals(course.average_gpa);
    return `
        <li class="${course.is_recent ? "" : "old"}">
            <div class="card rating-card mb-2">
                <div class="row no-gutters">
                    <a class="col-md-4 pl-3 pr-3 card-body d-flex justify-content-center justify-content-lg-start align-items-center rating-card-link" href="/course/${course.id}">
                        <div class="text-center text-lg-left">
                            <h3 id="title">${course.subdepartment.mnemonic} ${course.number}</h3>
                            <h5>${course.title}</h5>
                        </div>
                    </a>
                <div class="col-md-8">
                    <div class="card-body">
                        <div class="row justify-content-between text-center text-md-left">
                            <div class="col-4 col-lg-2 text-nowrap">
                                <small class="mb-0 text-uppercase">
                                    <i class="fa fa-star fa-fw" aria-hidden="true"></i>&nbsp;Rating
                                </small>
                                <p class="mb-0 info" id="rating">
                                    ${rating}
                                </p>
                            </div> 
                            <div class="col-4 col-lg-2 text-nowrap">
                                <small class="mb-0 text-uppercase">
                                    <i class="fa fa-dumbbell fa-fw" aria-hidden="true"></i>&nbsp;Difficulty
                                </small>
                                <p class="mb-0 info" id="difficulty">
                                    ${difficulty}
                                </p>
                            </div>
                            <div class="col-4 col-lg-2 text-nowrap">
                                <small class="mb-0 text-uppercase">
                                    <i class="fas fa-chart-bar" aria-hidden="true"></i>&nbsp;GPA
                                </small>
                                <p class="mb-0 info" id="gpa">${gpa}</p>
                            </div>
                            <div class="col-12 col-lg-3 offset-lg-3">
                                <small class="mb-0 text-uppercase">
                                    Last Taught
                                </small>
                                <p class="mb-0 info">${course.semester_last_taught.season} ${course.semester_last_taught.year}</p>
                            </div>
                        </div>
                            <p class="card-text mt-2">${course.description}</p>
                        </div>
                    </div>
                </div>
            </div>
        </li>
    `;
}

function emdashOrTwoDecimals(number) {
    // \u2014 is an em-dash
    return number === null ? "\u2014" : (Math.round(number * 100) / 100).toFixed(2);
}

function hideSpinner(subdepartmentId) {
    document.getElementById(`spinner-sd-${subdepartmentId}`).remove();
}

export { loadPage };
