-- Copy `email`s from CourseInstructorGrade to Instructor
UPDATE tcf_website_instructor AS i
SET email = cig.email
FROM tcf_website_courseinstructorgrade AS cig
WHERE i.email = ''
    AND cig.email <> ''
    AND cig.instructor_id = i.id;
