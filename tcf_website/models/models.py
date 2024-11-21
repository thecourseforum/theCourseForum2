# pylint: disable=missing-class-docstring, wildcard-import, fixme, too-many-lines
"""TCF Database models."""

import math

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.aggregates.general import ArrayAgg
from django.contrib.postgres.indexes import GinIndex
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import (
    Avg,
    Case,
    CharField,
    FloatField,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Abs, Coalesce, Round


class School(models.Model):
    """School model.

    Has many departments.
    """

    # School name. Required.
    name = models.CharField(max_length=255, unique=True)
    # Description of school. Optional.
    description = models.TextField(blank=True)
    # Website URL. Optional.
    website = models.URLField(blank=True)

    def __str__(self):
        """String representation of School."""
        return self.name


class Department(models.Model):
    """Department model.

    Belongs to a School.
    Has many Subdepartments.
    Has many Instructors.
    """

    # Department name. Required.
    name = models.CharField(max_length=255)
    # Department description. Optional.
    description = models.TextField(blank=True)
    # Website URL. Optional.
    website = models.URLField(blank=True)

    # School foreign key. Required.
    school = models.ForeignKey(School, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    # Fetches all courses in a department within the past `num_of_years' years
    def fetch_recent_courses(self, num_of_years: int = 5):
        """Return courses within last 'num_of_years' years."""
        latest_semester = Semester.latest()
        # to get the same season from n years earlier, subtract 10*n from semester number
        return Course.objects.filter(
            subdepartment__department=self,
            semester_last_taught__number__gte=latest_semester.number - (10 * num_of_years),
        ).order_by("number", "subdepartment__name")

    def sort_courses_by_key(self, annotation, num_of_years: int = 5, reverse: bool = False):
        """Sort recent courses by key `annotation`"""
        courses = self.fetch_recent_courses(num_of_years)
        sort_order = ("-" if reverse else "") + "sort_value"
        return courses.annotate(sort_value=Round(annotation, 10)).order_by(
            sort_order, "number", "subdepartment__name"
        )

    def sort_courses(self, sort_type: str, num_of_years: int = 5, order: str = "asc"):
        """Sort courses according by `sort_type`"""
        reverse = order != "asc"
        match sort_type:
            case "course_id":
                if reverse:
                    return self.fetch_recent_courses(num_of_years)[::-1]
                return self.fetch_recent_courses(num_of_years)
            # setting annotation
            # courses with no reviews put at bottom using Value()
            case "rating":
                annotation = Coalesce(
                    (
                        Avg("review__recommendability")
                        + Avg("review__instructor_rating")
                        + Avg("review__enjoyability")
                    )
                    / 3,
                    Value(0) if reverse else Value(5.1),
                    output_field=FloatField(),
                )
            case "difficulty":
                annotation = Coalesce(
                    Avg("review__difficulty"),
                    Value(0) if reverse else Value(5.1),
                    output_field=FloatField(),
                )
            case "gpa":
                annotation = Coalesce(
                    Avg("coursegrade__average"),
                    Value(0) if reverse else Value(4.1),
                    output_field=FloatField(),
                )

        return self.sort_courses_by_key(annotation, num_of_years, reverse)

    class Meta:
        indexes = [
            models.Index(fields=["school"]),
        ]

        constraints = [
            models.UniqueConstraint(fields=["name", "school"], name="unique departments per school")
        ]


# e.g. CREO in French department or ENCW in English


class Subdepartment(models.Model):
    """Subdepartment model.

    Belongs to a Department.
    Has many Courses.
    """

    # Subdepartment name. Required.
    name = models.CharField(max_length=255)
    # Subdepartment description. Optional.
    description = models.TextField(blank=True)
    # Subdepartment mnemonic. Required.
    mnemonic = models.CharField(max_length=255, unique=True)

    # Department foreign key. Required.
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.mnemonic} - {self.name}"

    def has_current_course(self):
        """Return True if subdepartment has a course in current semester."""
        return self.course_set.filter(section__semester=Semester.latest()).exists()

    class Meta:
        indexes = [
            models.Index(fields=["department"]),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["mnemonic", "department"],
                name="unique subdepartment mnemonics per department",
            )
        ]


class User(AbstractUser):
    """User model.

    Has many Reviews.
    """

    # User computing ID. Not required by database schema, but is
    # necessary. Should be created during authentication pipeline.
    computing_id = models.CharField(max_length=20, unique=True, blank=True)
    # User graduation year. Not required by database schema, but is
    # necessary. Should be created during authentication pipeline.
    graduation_year = models.IntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2999)],
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    def full_name(self):
        """Return string containing user full name."""
        return f"{self.first_name} {self.last_name}"

    def reviews(self):
        """Return user reviews sorted by creation date."""
        return self.review_set.annotate(
            sum_votes=models.functions.Coalesce(models.Sum("vote__value"), models.Value(0)),
            user_vote=models.functions.Coalesce(
                models.Sum("vote__value", filter=models.Q(vote__user=self)),
                models.Value(0),
            ),
        ).order_by("-created")


class Instructor(models.Model):
    """Instructor model.

    Belongs to many departments.
    Has many courses.
    Has many departments.
    """

    # Instructor first_name. Optional.
    first_name = models.CharField(max_length=255, blank=True)
    # Instructor last_name. Required.
    last_name = models.CharField(max_length=255)
    # Instructor full_name. Auto-populated.
    full_name = models.CharField(max_length=511, editable=False, blank=True)
    # Instructor email. Optional.
    email = models.EmailField(blank=True)
    # Instructor departments. Optional.
    departments = models.ManyToManyField(Department)
    # hidden professor. Required. Default visible.
    hidden = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    # this implementation is the same as average_rating in Course
    # except with an extra
    def average_rating_for_course(self, course):
        """Compute average rating for course.

        Rating is defined as the average of recommendability,
        instructor rating, and enjoyability."""
        ratings = Review.objects.filter(course=course, instructor=self).aggregate(
            models.Avg("recommendability"),
            models.Avg("instructor_rating"),
            models.Avg("enjoyability"),
        )

        recommendability = ratings.get("recommendability__avg")
        instructor_rating = ratings.get("instructor_rating__avg")
        enjoyability = ratings.get("enjoyability__avg")

        # Return None if one component is absent.
        if not recommendability or not instructor_rating or not enjoyability:
            return None

        return (recommendability + instructor_rating + enjoyability) / 3

    def average_difficulty_for_course(self, course):
        """Compute average difficulty score."""
        return Review.objects.filter(course=course, instructor=self).aggregate(
            models.Avg("difficulty")
        )["difficulty__avg"]

    def average_enjoyability_for_course(self, course):
        """Computer average enjoyability"""
        return Review.objects.filter(course=course, instructor=self).aggregate(
            models.Avg("enjoyability")
        )["enjoyability__avg"]

    def average_instructor_rating_for_course(self, course):
        """Computer average instructor rating"""
        return Review.objects.filter(course=course, instructor=self).aggregate(
            models.Avg("instructor_rating")
        )["instructor_rating__avg"]

    def average_recommendability_for_course(self, course):
        """Computer average recommendability"""
        return Review.objects.filter(course=course, instructor=self).aggregate(
            models.Avg("recommendability")
        )["recommendability__avg"]

    def average_hours_for_course(self, course):
        """Compute average hrs/wk."""
        return Review.objects.filter(course=course, instructor=self).aggregate(
            models.Avg("hours_per_week")
        )["hours_per_week__avg"]

    def average_reading_hours_for_course(self, course):
        """Compute average reading hrs/wk."""
        return Review.objects.filter(course=course, instructor=self).aggregate(
            models.Avg("amount_reading")
        )["amount_reading__avg"]

    def average_writing_hours_for_course(self, course):
        """Compute average writing hrs/wk."""
        return Review.objects.filter(course=course, instructor=self).aggregate(
            models.Avg("amount_writing")
        )["amount_writing__avg"]

    def average_group_hours_for_course(self, course):
        """Compute average group work hrs/wk."""
        return Review.objects.filter(course=course, instructor=self).aggregate(
            models.Avg("amount_group")
        )["amount_group__avg"]

    def average_other_hours_for_course(self, course):
        """Compute average other HW hrs/wk."""
        return Review.objects.filter(course=course, instructor=self).aggregate(
            models.Avg("amount_homework")
        )["amount_homework__avg"]

    def average_gpa_for_course(self, course):
        """Compute average GPA"""
        return CourseInstructorGrade.objects.filter(course=course, instructor=self).aggregate(
            models.Avg("average")
        )["average__avg"]

    def taught_courses(self):
        """Returns all sections taught by Instructor."""
        # this method is very inefficient and doesn't actually do what the name
        # implies (collecting Sections instead of Courses); work in progress
        return Section.objects.filter(instructors=self)

    def average_rating(self):
        """Compute average rating for all this Instructor's Courses"""
        ratings = Review.objects.filter(instructor=self).aggregate(
            models.Avg("recommendability"),
            models.Avg("instructor_rating"),
            models.Avg("enjoyability"),
        )

        recommendability = ratings.get("recommendability__avg")
        instructor_rating = ratings.get("instructor_rating__avg")
        enjoyability = ratings.get("enjoyability__avg")

        # Return None if one component is absent.
        if not recommendability or not instructor_rating or not enjoyability:
            return None

        return (recommendability + instructor_rating + enjoyability) / 3

    def average_difficulty(self):
        """Compute average difficulty for all this Instructor's Courses"""
        return Review.objects.filter(instructor=self).aggregate(models.Avg("difficulty"))[
            "difficulty__avg"
        ]

    def average_gpa(self):
        """Compute average GPA for all this Instructor's Courses"""
        return CourseInstructorGrade.objects.filter(instructor=self).aggregate(
            models.Avg("average")
        )["average__avg"]

    def save(self, *args, **kwargs):
        self.full_name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            GinIndex(
                fields=["first_name"], opclasses=["gin_trgm_ops"], name="first_name_instructor"
            ),
            GinIndex(fields=["last_name"], opclasses=["gin_trgm_ops"], name="last_name_instructor"),
            GinIndex(fields=["full_name"], opclasses=["gin_trgm_ops"], name="full_name_instructor"),
        ]


class Semester(models.Model):
    """Semester model.

    Has many Sections.
    Can belong to many Courses.
    """

    # Enumeration of possible seasons.
    SEASONS = (
        ("FALL", "Fall"),
        ("JANUARY", "January"),
        ("SPRING", "Spring"),
        ("SUMMER", "Summer"),
    )

    # Semester year. Required.
    year = models.IntegerField(validators=[MinValueValidator(2000), MaxValueValidator(2999)])
    # Semester season. Required.
    season = models.CharField(max_length=7, choices=SEASONS)

    """
    Semester number as defined by SIS and Lou's List. Required.

    e.g. Semester 1208

    1 - Always the first digit.
    20 - Year (2020).
    8 - First month of season (August, so Fall).

    Other examples:
    1191 - January 2019
    1182 - Spring 2018
    1166 - Summer 2016.
    """
    number = models.IntegerField(help_text="As defined in SIS/Lou's List", unique=True)

    def __repr__(self):
        return f"{self.year} {self.season.title()} ({self.number})"

    def __str__(self):
        return f"{self.season.title()} {self.year}"

    def is_after(self, other_sem):
        """Returns True if semester occurred later than other_semester."""
        return self.number > other_sem.number

    @staticmethod
    def latest():
        """Returns the latest semester."""
        return Semester.objects.order_by("-number").first()

    class Meta:
        indexes = [
            models.Index(fields=["year", "season"]),
            models.Index(fields=["number"]),
        ]

        constraints = [models.UniqueConstraint(fields=["season", "year"], name="unique semesters")]


class Discipline(models.Model):
    """Discipline model.

    Has many Courses.
    """

    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    """Course model.

    Belongs to a Subdepartment.
    Has many Sections.
    Has a Semester last taught.
    """

    # Course title. Required.
    title = models.CharField(max_length=255)
    # Course description. Optional.
    description = models.TextField(blank=True)
    # Course disciplines. Optional.
    disciplines = models.ManyToManyField(Discipline, blank=True)

    # Course number. Required.
    number = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99999)])

    # Subdepartment foreign key. Required.
    subdepartment = models.ForeignKey(Subdepartment, on_delete=models.CASCADE)
    # Semester that the course was most recently taught.
    semester_last_taught = models.ForeignKey(Semester, on_delete=models.CASCADE)
    # Subdepartment mnemonic and course number. Required.
    combined_mnemonic_number = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.subdepartment.mnemonic} {self.number} | {self.title}"

    def save(self, *args, **kwargs):
        self.combined_mnemonic_number = f"{self.subdepartment.mnemonic} {self.number}".strip()
        super().save(*args, **kwargs)

    def compute_pre_req(self):
        """Returns course pre-requisite(s)."""
        return self.parse_course_description()[0]

    def course_description_without_pre_req(self):
        """Returns course description without its pre-requisite(s)."""
        return self.parse_course_description()[1]

    def parse_course_description(self):
        """Returns a tuple with pre-requisite(s)
        and course description without the pre-requisite(s)."""
        # When no pre-req
        course_description_without_pre_req = self.description
        pre_req = ""
        if "Prerequisite" in self.description:
            # Get pre_req from beginning to end
            from_pre_req_to_end = self.description[self.description.find("Prerequisite") :]
            # Get rid of title of "Prerequisite"
            pre_req_no_title = from_pre_req_to_end[from_pre_req_to_end.find(":") + 1 :]

            # Check if in-line or not for pre_req
            if pre_req_no_title.find(".") > 0:
                pre_req = pre_req_no_title[: pre_req_no_title.find(".")]
            else:
                pre_req = pre_req_no_title

            # Check whether it is inline or at end for extracting course_description_without_pre_req
            if from_pre_req_to_end.find(".") > 0:
                course_description_without_pre_req = self.description.replace(
                    from_pre_req_to_end[: from_pre_req_to_end.find(".") + 1], ""
                )
            else:
                course_description_without_pre_req = self.description.replace(
                    from_pre_req_to_end, ""
                )

        return (pre_req, course_description_without_pre_req)

    def code(self):
        """Returns the courses code string."""
        return f"{self.subdepartment.mnemonic} {self.number}"

    def eval_link(self):
        """Returns link to student eval page for that class"""
        link = (
            f"https://evals.itc.virginia.edu/course-selectionguide/pages/SGMain.jsp?cmp="
            f"{self.subdepartment.mnemonic},{self.number}"
        )
        return link

    def is_recent(self):
        """Returns True if course was taught in current semester."""
        return self.semester_last_taught == Semester.latest()

    def average_rating(self):
        """Compute average rating.

        Rating is defined as the average of recommendability,
        instructor rating, and enjoyability."""
        ratings = Review.objects.filter(course=self).aggregate(
            models.Avg("recommendability"),
            models.Avg("instructor_rating"),
            models.Avg("enjoyability"),
        )

        recommendability = ratings.get("recommendability__avg")
        instructor_rating = ratings.get("instructor_rating__avg")
        enjoyability = ratings.get("enjoyability__avg")

        # Return None if one component is absent.
        if not recommendability or not instructor_rating or not enjoyability:
            return None

        return (recommendability + instructor_rating + enjoyability) / 3

    def average_difficulty(self):
        """Compute average difficulty score."""
        return Review.objects.filter(course=self).aggregate(models.Avg("difficulty"))[
            "difficulty__avg"
        ]

    def average_gpa(self):
        """Compute average GPA."""
        return CourseGrade.objects.filter(course=self).aggregate(models.Avg("average"))[
            "average__avg"
        ]

    def review_count(self):
        """Compute total number of course reviews."""
        return self.review_set.count()

    def get_instructors_and_data(self, latest_semester, reverse):
        # https://docs.djangoproject.com/en/5.0/ref/models/expressions/
        """Annotate each instructor with the id of the semester last taught object
        Those pks are converted to semester objects with the second annotation
        """

        semester_last_taught_subquery = Subquery(
            Section.objects.filter(course=self, instructors=OuterRef("pk"))
            .order_by("-semester__number")
            .values("semester__id")[:1]
        )

        instructors = (
            Instructor.objects.filter(section__course=self, hidden=False)
            .distinct()
            .annotate(
                gpa=Coalesce(
                    Avg(
                        "courseinstructorgrade__average",
                        filter=Q(courseinstructorgrade__course=self),
                    ),
                    Value(math.inf) if reverse else Value(-1),
                    output_field=FloatField(),
                ),
                difficulty=Coalesce(
                    Avg("review__difficulty", filter=Q(review__course=self)),
                    Value(math.inf) if reverse else Value(-1),
                    output_field=FloatField(),
                ),
                rating=Coalesce(
                    (
                        Avg(
                            "review__instructor_rating",
                            filter=Q(review__course=self),
                        )
                        + Avg(
                            "review__enjoyability",
                            filter=Q(review__course=self),
                        )
                        + Avg(
                            "review__recommendability",
                            filter=Q(review__course=self),
                        )
                    )
                    / 3,
                    # invalid value for if there are no reviews
                    Value(math.inf) if reverse else Value(-1),
                    output_field=FloatField(),
                ),
                semester_last_taught=semester_last_taught_subquery,
                # ArrayAgg:
                # https://docs.djangoproject.com/en/3.2/ref/contrib/postgres/aggregates/#arrayagg
                section_times=ArrayAgg(
                    Case(
                        When(
                            section__semester=latest_semester,
                            then="section__section_times",
                        ),
                        output_field=CharField(),
                    ),
                    distinct=True,
                ),
                section_nums=ArrayAgg(
                    Case(
                        When(
                            section__semester=latest_semester,
                            then="section__sis_section_number",
                        ),
                        output_field=CharField(),
                    ),
                    distinct=True,
                ),
            )
        )

        return instructors

    def sort_instructors_by_key(
        self,
        latest_semester: Semester,
        recent: bool,
        order: str,
        sortby: str,
    ):
        """Sort instructors by `sortby`"""
        reverse = order != "desc"
        instructors = self.get_instructors_and_data(latest_semester, reverse)

        sort_field = {
            "gpa": "gpa",
            "rating": "rating",
            "difficulty": "difficulty",
            "last_taught": "semester_last_taught",
        }.get(sortby, "semester_last_taught")

        order_prefix = "" if reverse else "-"

        if recent:
            instructors = instructors.filter(semester_last_taught=Semester.latest().pk)

        instructors = instructors.order_by(order_prefix + sort_field)
        return instructors

    @classmethod
    def filter_by_time(cls, days=None, start_time=None, end_time=None):
        """Filter courses by available times."""
        query = cls.objects.all()

        if days:
            # Get the latest semester
            current_semester = Semester.latest()

            # Map day codes to field names
            day_map = {
                "MON": "monday",
                "TUE": "tuesday",
                "WED": "wednesday",
                "THU": "thursday",
                "FRI": "friday",
            }

            # Get all possible days
            all_days = set(day_map.values())  # {monday, tuesday, wednesday, thursday, friday}
            # Get selected days
            selected_days = {day_map[d] for d in days if d in day_map}  # {monday, wednesday}
            # Get unavailable days
            unavailable_days = all_days - selected_days  # {tuesday, thursday, friday}

            # Filter for sections that don't meet on unavailable days
            section_conditions = Q(section__semester=current_semester)

            for day in unavailable_days:
                section_conditions &= Q(**{f"section__sectiontime__{day}": False})

            if start_time:
                section_conditions &= Q(section__sectiontime__start_time__gte=start_time)
            if end_time:
                section_conditions &= Q(section__sectiontime__end_time__lte=end_time)

            query = query.filter(section_conditions)

        return query.distinct()

    class Meta:
        indexes = [
            GinIndex(
                fields=["combined_mnemonic_number"],
                opclasses=["gin_trgm_ops"],
                name="course_mnemonic_number",
            ),
            GinIndex(
                fields=["title"],
                opclasses=["gin_trgm_ops"],
                name="title_gin_index",
            ),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["subdepartment", "number"],
                name="unique course subdepartment and number",
            )
        ]


class CourseGrade(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    average = models.FloatField(default=0.0, null=True)
    a_plus = models.IntegerField(default=0)
    a = models.IntegerField(default=0)
    a_minus = models.IntegerField(default=0)
    b_plus = models.IntegerField(default=0)
    b = models.IntegerField(default=0)
    b_minus = models.IntegerField(default=0)
    c_plus = models.IntegerField(default=0)
    c = models.IntegerField(default=0)
    c_minus = models.IntegerField(default=0)
    dfw = models.IntegerField(default=0)
    total_enrolled = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.course.subdepartment.mnemonic} {self.course.number} {self.average}"


class CourseInstructorGrade(models.Model):
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    average = models.FloatField(default=0.0, null=True)
    a_plus = models.IntegerField(default=0)
    a = models.IntegerField(default=0)
    a_minus = models.IntegerField(default=0)
    b_plus = models.IntegerField(default=0)
    b = models.IntegerField(default=0)
    b_minus = models.IntegerField(default=0)
    c_plus = models.IntegerField(default=0)
    c = models.IntegerField(default=0)
    c_minus = models.IntegerField(default=0)
    dfw = models.IntegerField(default=0)
    total_enrolled = models.IntegerField(default=0)

    def __str__(self):
        return (
            f"{self.instructor.first_name} {self.instructor.last_name} "
            f"{self.course.subdepartment.mnemonic} {self.course.number} {self.average}"
        )


class Section(models.Model):
    """Section model.

    Belongs to a Course.
    Has many Instructors.
    Has a Semester.
    """

    # Section number as listed on SIS/Lou's List. Required.
    sis_section_number = models.IntegerField()  # NOTE: not unique!
    # Section instructors. Optional.
    instructors = models.ManyToManyField(Instructor)

    # Section Semester foreign key. Required.
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    # Section Course foreign key. Required.
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    # Section topic. Optional. E.g. for CS 4501, each section has a
    # different topic.
    topic = models.TextField(blank=True)

    # Section cost. Optional. e.g. 'No Cost Course Materials' or 'Low Cost Course Materials'.
    cost = models.CharField(max_length=255, blank=True)

    # Section # of units. Optional.
    units = models.CharField(max_length=10, blank=True)
    # Section section_type. Optional. e.g. 'lec' or 'lab'.
    section_type = models.CharField(max_length=255, blank=True)

    # Comma-separated list of times the section is taught.
    section_times = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return (
            f"{self.course} | {self.semester} | "
            f"{', '.join(str(i) for i in self.instructors.all())}"
        )

    class Meta:
        indexes = [
            models.Index(fields=["semester", "course"]),
            models.Index(fields=["course"]),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["sis_section_number", "semester"],
                name="unique sections per semesters",
            )
        ]


class SectionTime(models.Model):
    """Section meeting time model.

    Belongs to a Section.
    """

    section = models.ForeignKey("Section", on_delete=models.CASCADE)

    # Individual day fields
    monday = models.BooleanField(default=False)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)

    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        days = []
        if self.monday:
            days.append("MON")
        if self.tuesday:
            days.append("TUE")
        if self.wednesday:
            days.append("WED")
        if self.thursday:
            days.append("THU")
        if self.friday:
            days.append("FRI")
        return f"{','.join(days)} {self.start_time}-{self.end_time}"

    @property
    def days_list(self):
        """Return list of days this section meets."""
        days = []
        if self.monday:
            days.append("MON")
        if self.tuesday:
            days.append("TUE")
        if self.wednesday:
            days.append("WED")
        if self.thursday:
            days.append("THU")
        if self.friday:
            days.append("FRI")
        return days

    class Meta:
        indexes = [
            models.Index(fields=["monday"]),
            models.Index(fields=["tuesday"]),
            models.Index(fields=["wednesday"]),
            models.Index(fields=["thursday"]),
            models.Index(fields=["friday"]),
            models.Index(fields=["start_time"]),
            models.Index(fields=["end_time"]),
        ]


class Review(models.Model):
    """Review model.

    Belongs to a User.
    Has a Course.
    Has an Instructor.
    Has an Semester.
    """

    # Review text. Optional.
    text = models.TextField(blank=True)
    # Review user foreign key. Required.
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Review course foreign key. Required.
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    # Review instructor foreign key. Required.
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    # Review semester foreign key. Required.
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    # Email of reviewer for Review Drive, should be blank most of the time
    # Only done for reviews without accounts
    email = models.CharField(default="", null=True, blank=True)

    # Enum of Rating options.
    RATINGS = (
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 5),
    )
    # Review instructor rating. Required.
    instructor_rating = models.PositiveSmallIntegerField(choices=RATINGS)
    # Review difficulty. Required.
    difficulty = models.PositiveSmallIntegerField(choices=RATINGS)
    # Review recommendability. Required.
    recommendability = models.PositiveSmallIntegerField(choices=RATINGS)
    # Review enjoyability. Required.
    enjoyability = models.PositiveSmallIntegerField(choices=RATINGS)

    # Review hours per week. Required.
    # hours_per_week used to be the only thing, but we also brought back the
    # subcategories. This is just a sum, but I'm keeping it because other parts
    # of the codebase depend on this model field existing and I'm not fixing them.
    # TODO: make validators/tests to ensure hours_per_week is the sum, or just
    #  remove it entirely from the model and replace w/ function
    hours_per_week = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(80)]
    )
    # Review hours of reading per week. Required.
    amount_reading = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    # Review hours of writing per week. Required.
    amount_writing = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    # Review hours of group work per week. Required.
    amount_group = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    # Review hours of homework per week. Required.
    amount_homework = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )

    # Review created date. Required.
    created = models.DateTimeField(auto_now_add=True)
    # Review modified date. Required.
    modified = models.DateTimeField(auto_now=True)

    # Review visibility. Required. Default visible.
    hidden = models.BooleanField(default=False)

    # does this get used anywhere? not sure
    def average(self):
        """Average score for review."""
        return (self.instructor_rating + self.recommendability + self.enjoyability) / 3

    def count_votes(self):
        """Sum votes for review."""
        return self.vote_set.aggregate(
            upvotes=Coalesce(models.Sum("value", filter=models.Q(value=1)), 0),
            downvotes=Coalesce(Abs(models.Sum("value", filter=models.Q(value=-1))), 0),
        )

    def upvote(self, user):
        """Create an upvote."""

        # Check if already upvoted.
        upvoted = Vote.objects.filter(
            user=user,
            review=self,
            value=1,
        ).exists()

        # Delete all prior votes.
        Vote.objects.filter(
            user=user,
            review=self,
        ).delete()

        # Don't upvote again if previously upvoted.
        if upvoted:
            return

        Vote.objects.create(
            value=1,
            user=user,
            review=self,
        )

    def downvote(self, user):
        """Create a downvote."""

        # Check if already downvoted.
        downvoted = Vote.objects.filter(
            user=user,
            review=self,
            value=-1,
        ).exists()

        # Delete all prior votes.
        Vote.objects.filter(
            user=user,
            review=self,
        ).delete()

        # Don't downvote again if previously downvoted.
        if downvoted:
            return

        Vote.objects.create(
            value=-1,
            user=user,
            review=self,
        )

    @staticmethod
    def display_reviews(course_id, instructor_id, user):
        """Prepare review list for course-instructor page."""
        reviews = (
            Review.objects.filter(instructor=instructor_id, course=course_id, hidden=False)
            .exclude(text="")
            .annotate(
                sum_votes=models.functions.Coalesce(models.Sum("vote__value"), models.Value(0)),
            )
        )
        if user.is_authenticated:
            reviews = reviews.annotate(
                user_vote=models.functions.Coalesce(
                    models.Sum("vote__value", filter=models.Q(vote__user=user)),
                    models.Value(0),
                ),
            )
        return reviews.order_by("-created")

    def __str__(self):
        return f"Review by {self.user} for {self.course} taught by {self.instructor}"

    class Meta:
        # Improve scanning of reviews by course and instructor.
        indexes = [
            models.Index(fields=["course", "instructor"]),
            models.Index(fields=["user", "-created"]),
        ]

        # Some of the tCF 1.0 data did not honor this constraint.
        # Should we add it and remove duplicates from old data?
        # - Sounds good, just keep the newer review - Jennifer

    #     constraints = [
    #         models.UniqueConstraint(
    #             fields=['user', 'course', 'instructor'],
    #             name='unique review per user, course, and instructor',
    #         )
    #     ]


class Vote(models.Model):
    """Vote model.

    Belongs to a User.
    Has a review.
    """

    # Vote value. Required.
    value = models.IntegerField(validators=[MinValueValidator(-1), MaxValueValidator(1)])
    # Vote user foreign key. Required.
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Vote review foreign key. Required.
    review = models.ForeignKey(Review, on_delete=models.CASCADE)

    def __str__(self):
        return f"Vote of value {self.value} for {self.review} by {self.user}"

    class Meta:
        indexes = [
            models.Index(fields=["review"]),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "review"],
                name="unique vote per user and review",
            )
        ]


class Question(models.Model):
    """Question model.
    Belongs to a User.
    Has a course and instructor.
    """

    text = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, default=None)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Question for {self.course}"

    def count_votes(self):
        """Sum votes for review."""
        return self.votequestion_set.aggregate(
            upvotes=Coalesce(models.Sum("value", filter=models.Q(value=1)), 0),
            downvotes=Coalesce(Abs(models.Sum("value", filter=models.Q(value=-1))), 0),
        )

    def upvote(self, user):
        """Create an upvote."""

        # Check if already upvoted.
        upvoted = VoteQuestion.objects.filter(
            user=user,
            question=self,
            value=1,
        ).exists()

        # Delete all prior votes.
        VoteQuestion.objects.filter(
            user=user,
            question=self,
        ).delete()

        # Don't upvote again if previously upvoted.
        if upvoted:
            return

        VoteQuestion.objects.create(
            value=1,
            user=user,
            question=self,
        )

    def downvote(self, user):
        """Create a downvote."""

        # Check if already downvoted.
        downvoted = VoteQuestion.objects.filter(
            user=user,
            question=self,
            value=-1,
        ).exists()

        # Delete all prior votes.
        VoteQuestion.objects.filter(
            user=user,
            question=self,
        ).delete()

        # Don't downvote again if previously downvoted.
        if downvoted:
            return

        VoteQuestion.objects.create(
            value=-1,
            user=user,
            question=self,
        )

    @staticmethod
    def display_activity(course_id, instructor_id, user):
        """Prepare review list for course-instructor page."""
        question = (
            Question.objects.filter(instructor=instructor_id, course=course_id)
            .exclude(text="")
            .annotate(
                sum_q_votes=models.functions.Coalesce(
                    models.Sum("votequestion__value"), models.Value(0)
                ),
            )
        )
        if user.is_authenticated:
            question = question.annotate(
                user_q_vote=models.functions.Coalesce(
                    models.Sum(
                        "votequestion__value",
                        filter=models.Q(votequestion__user=user),
                    ),
                    models.Value(0),
                ),
            )
        return question.order_by("-created")


class Answer(models.Model):
    """Answer model.
    Belongs to a User.
    Has a question.
    """

    text = models.TextField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, default=None)

    def __str__(self):
        return f"Answer for {self.question}"

    def count_votes(self):
        """Sum votes for answers."""
        return self.voteanswer_set.aggregate(
            upvotes=Coalesce(models.Sum("value", filter=models.Q(value=1)), 0),
            downvotes=Coalesce(Abs(models.Sum("value", filter=models.Q(value=-1))), 0),
        )

    def upvote(self, user):
        """Create an upvote."""

        # Check if already upvoted.
        upvoted = VoteAnswer.objects.filter(
            user=user,
            answer=self,
            value=1,
        ).exists()

        # Delete all prior votes.
        VoteAnswer.objects.filter(
            user=user,
            answer=self,
        ).delete()

        # Don't upvote again if previously upvoted.
        if upvoted:
            return

        VoteAnswer.objects.create(
            value=1,
            user=user,
            answer=self,
        )

    def downvote(self, user):
        """Create a downvote."""

        # Check if already downvoted.
        downvoted = VoteAnswer.objects.filter(
            user=user,
            answer=self,
            value=-1,
        ).exists()

        # Delete all prior votes.
        VoteAnswer.objects.filter(
            user=user,
            answer=self,
        ).delete()

        # Don't downvote again if previously downvoted.
        if downvoted:
            return

        VoteAnswer.objects.create(
            value=-1,
            user=user,
            answer=self,
        )

    @staticmethod
    def display_activity(question_id, user):
        """Prepare answers for course-instructor page."""
        answer = (
            Answer.objects.filter(question=question_id)
            .exclude(text="")
            .annotate(
                sum_a_votes=models.functions.Coalesce(
                    models.Sum("voteanswer__value"), models.Value(0)
                ),
            )
        )
        if user.is_authenticated:
            answer = answer.annotate(
                user_a_vote=models.functions.Coalesce(
                    models.Sum(
                        "voteanswer__value",
                        filter=models.Q(voteanswer__user=user),
                    ),
                    models.Value(0),
                ),
            )
        return answer.order_by("-created")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "question"],
                name="unique answer per user and question",
            )
        ]


class VoteQuestion(models.Model):
    """Vote model.

    Belongs to a User.
    Has a question.
    """

    # Vote value. Required.
    value = models.IntegerField(validators=[MinValueValidator(-1), MaxValueValidator(1)])
    # Vote user foreign key. Required.
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Vote question foreign key. Required.
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    def __str__(self):
        return f"Vote of value {self.value} for {self.question} by {self.user}"

    class Meta:
        indexes = [
            models.Index(fields=["question"]),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "question"],
                name="unique vote per user and question",
            )
        ]


class VoteAnswer(models.Model):
    """Vote model.

    Belongs to a User.
    Has a question.
    """

    # Vote value. Required.
    value = models.IntegerField(validators=[MinValueValidator(-1), MaxValueValidator(1)])
    # Vote user foreign key. Required.
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Vote answer foreign key. Required.
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)

    def __str__(self):
        return f"Vote of value {self.value} for {self.answer} by {self.user}"

    class Meta:
        indexes = [
            models.Index(fields=["answer"]),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "answer"],
                name="unique vote per user and answer",
            )
        ]
