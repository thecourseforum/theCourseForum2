-- Copy `email`s from CourseInstructorGrade to Instructor
-- assuming instructor names are unique
UPDATE tcf_website_instructor AS i
SET email = cig.email
FROM tcf_website_courseinstructorgrade AS cig
WHERE i.email = ''
    AND cig.email <> ''
    AND cig.last_name = i.last_name
    AND cig.first_name = i.first_name;
