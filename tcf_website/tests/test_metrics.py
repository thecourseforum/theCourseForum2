# Save this to a file named test_metrics.py or run directly in the Django shell

import random

from django.db import transaction

from tcf_website.models.models import (
    Course,
    CourseInstructorMetrics,
    Instructor,
    Review,
    Semester,
    User,
)


def test_metrics():
    """Test review metrics calculation and update logic."""
    print("==== Testing Course-Instructor Metrics ====")

    # 1. Check existing metrics
    cim_count = CourseInstructorMetrics.objects.count()
    courses_with_metrics = Course.objects.exclude(avg_rating=None).count()

    print(f"Total CourseInstructorMetrics objects: {cim_count}")
    print(f"Total Courses with metrics: {courses_with_metrics}")

    # 2. Get a random course with metrics for testing
    course = Course.objects.exclude(avg_rating=None).order_by("?").first()
    if not course:
        print("No courses with metrics found.")
        return

    print(f"\nTest Course: {course}")
    print(f"Rating: {course.avg_rating}")
    print(f"Difficulty: {course.avg_difficulty}")
    print(f"Hours per week: {course.avg_hours_per_week}")
    print(f"Review count field: {course.review_count}")
    print(f"Calculated review count: {course.get_review_count()}")

    # 3. Get an instructor who has taught this course
    instructor = Instructor.objects.filter(section__course=course).first()
    if not instructor:
        print("No instructors found for this course.")
        return

    print(f"\nTest Instructor: {instructor}")

    # 4. Get metrics for this course-instructor pair
    try:
        ci_metrics = CourseInstructorMetrics.objects.get(course=course, instructor=instructor)
        print(f"Course-Instructor metrics found!")
        print(f"Rating: {ci_metrics.avg_rating}")
        print(f"Difficulty: {ci_metrics.avg_difficulty}")
        print(f"Review count: {ci_metrics.review_count}")
    except CourseInstructorMetrics.DoesNotExist:
        print("No metrics found for this course-instructor pair.")

    # 5. Test creating a new review
    print("\n==== Testing Review Creation ====")

    # Get a user for testing
    user = User.objects.first()
    if not user:
        print("No users found for testing.")
        return

    # Get a semester for testing
    semester = Semester.objects.first()
    if not semester:
        print("No semesters found for testing.")
        return

    # Store initial metrics for comparison
    initial_course_rating = course.avg_rating
    initial_course_difficulty = course.avg_difficulty
    initial_course_hours = course.avg_hours_per_week
    initial_course_review_count = course.review_count

    # Create new review
    with transaction.atomic():
        try:
            review = Review(
                course=course,
                instructor=instructor,
                user=user,
                semester=semester,  # Required field
                text="This is a test review created to verify metrics calculation",
                difficulty=4,
                recommendability=5,
                enjoyability=5,
                instructor_rating=5,
                hours_per_week=12,
                amount_reading=3,
                amount_writing=2,
                amount_group=1,
                amount_homework=6,
            )
            review.save()
            print("Test review created successfully!")
        except Exception as e:
            print(f"Error creating review: {e}")
            return

    # Reload course to get updated metrics
    course.refresh_from_db()

    print("\n==== Updated Metrics ====")

    initial_course_review_count = course.review_count

    print(f"Course Rating: {initial_course_rating} → {course.avg_rating}")
    print(f"Course Difficulty: {initial_course_difficulty} → {course.avg_difficulty}")
    print(f"Course Hours: {initial_course_hours} → {course.avg_hours_per_week}")
    print(f"Course Review Count: {initial_course_review_count} → {course.review_count}")

    # Check updated course-instructor metrics
    try:
        ci_metrics = CourseInstructorMetrics.objects.get(course=course, instructor=instructor)
        print(f"\nCourse-Instructor Rating: {ci_metrics.avg_rating}")
        print(f"Course-Instructor Difficulty: {ci_metrics.avg_difficulty}")
        print(f"Course-Instructor Review Count: {ci_metrics.review_count}")
    except CourseInstructorMetrics.DoesNotExist:
        print("No metrics found for this course-instructor pair.")

    # Clean up - delete the test review
    review.delete()
    print("\nTest review deleted.")

    # Verify metrics were restored
    course.refresh_from_db()
    print("\n==== Restored Metrics ====")
    print(f"Course Rating: {course.avg_rating}")
    print(f"Course Review Count: {course.review_count}")

    print("\nTest completed!")


if __name__ == "__main__":
    test_metrics()
