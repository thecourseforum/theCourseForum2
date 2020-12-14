-- Copy missing `instructor_id` from Instructor to CourseInstructorGrade
-- assuming instructor names are unique
UPDATE tcf_website_courseinstructorgrade AS cig
SET instructor_id = i.id
FROM tcf_website_instructor AS i
WHERE cig.instructor_id IS NULL
    AND cig.last_name = i.last_name
    AND cig.first_name = i.first_name;
