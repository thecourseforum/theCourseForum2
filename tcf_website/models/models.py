# pylint: disable=missing-class-docstring, wildcard-import, fixme

"""TCF Database models."""

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


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

    class Meta:
        indexes = [
            models.Index(fields=['school']),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=['name', 'school'],
                name='unique departments per school'
            )
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

    def recent_courses(self):
        """Return courses within last 5 years."""
        latest_semester = Semester.latest()
        return self.course_set.filter(
            semester_last_taught__year__gte=latest_semester.year -
            5).order_by("number")

    def has_current_course(self):
        """Return True if subdepartment has a course in current semester."""
        return self.course_set.filter(
            section__semester=Semester.latest()).exists()

    class Meta:
        indexes = [
            models.Index(fields=['department']),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=['mnemonic', 'department'],
                name='unique subdepartment mnemonics per department'
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
        blank=True, null=True
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    def full_name(self):
        """Return string containing user full name."""
        return f"{self.first_name} {self.last_name}"

    def reviews(self):
        """Return user reviews sorted by creation date."""
        return self.review_set.annotate(
            sum_votes=models.functions.Coalesce(
                models.Sum('vote__value'),
                models.Value(0)
            ),
            user_vote=models.functions.Coalesce(
                models.Sum('vote__value',
                           filter=models.Q(vote__user=self)),
                models.Value(0)
            )
        ).order_by('-created')


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
    # Instructor email. Optional.
    email = models.EmailField(blank=True)
    # Instructor website. Optional.
    website = models.URLField(blank=True)
    # Instructor departments. Optional.
    departments = models.ManyToManyField(Department)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    def full_name(self):
        """Return string containing instructor full name."""
        return f"{self.first_name} {self.last_name}"

    # this implementation is the same as average_rating in Course
    # except with an extra
    def average_rating_for_course(self, course):
        """Compute average rating for course.

        Rating is defined as the average of recommendability,
        instructor rating, and enjoyability."""
        ratings = Review.objects.filter(
            course=course, instructor=self).aggregate(
            models.Avg('recommendability'),
            models.Avg('instructor_rating'),
            models.Avg('enjoyability'))

        recommendability = ratings.get('recommendability__avg')
        instructor_rating = ratings.get('instructor_rating__avg')
        enjoyability = ratings.get('enjoyability__avg')

        # Return None if one component is absent.
        if not recommendability or not instructor_rating or not enjoyability:
            return None

        return (recommendability + instructor_rating + enjoyability) / 3

    def average_difficulty_for_course(self, course):
        """Compute average difficulty score."""
        return Review.objects.filter(
            course=course, instructor=self).aggregate(
            models.Avg('difficulty'))['difficulty__avg']

    def average_enjoyability_for_course(self, course):
        """Computer average enjoyability"""
        return Review.objects.filter(
            course=course, instructor=self).aggregate(
            models.Avg('enjoyability'))['enjoyability__avg']

    def average_instructor_rating_for_course(self, course):
        """Computer average instructor rating"""
        return Review.objects.filter(
            course=course, instructor=self).aggregate(
            models.Avg('instructor_rating'))['instructor_rating__avg']

    def average_recommendability_for_course(self, course):
        """Computer average recommendability"""
        return Review.objects.filter(
            course=course, instructor=self).aggregate(
            models.Avg('recommendability'))['recommendability__avg']

    def average_hours_for_course(self, course):
        """Compute average hrs/wk."""
        return Review.objects.filter(
            course=course, instructor=self).aggregate(
            models.Avg('hours_per_week'))['hours_per_week__avg']

    def average_reading_hours_for_course(self, course):
        """Compute average reading hrs/wk."""
        return Review.objects.filter(
            course=course, instructor=self).aggregate(
            models.Avg('amount_reading'))['amount_reading__avg']

    def average_writing_hours_for_course(self, course):
        """Compute average writing hrs/wk."""
        return Review.objects.filter(
            course=course, instructor=self).aggregate(
            models.Avg('amount_writing'))['amount_writing__avg']

    def average_group_hours_for_course(self, course):
        """Compute average group work hrs/wk."""
        return Review.objects.filter(
            course=course, instructor=self).aggregate(
            models.Avg('amount_group'))['amount_group__avg']

    def average_other_hours_for_course(self, course):
        """Compute average other HW hrs/wk."""
        return Review.objects.filter(
            course=course, instructor=self).aggregate(
            models.Avg('amount_homework'))['amount_homework__avg']

    def average_gpa_for_course(self, course):
        """Compute average GPA"""
        return CourseInstructorGrade.objects.filter(
            course=course, instructor=self).aggregate(
            models.Avg('average'))['average__avg']

    def taught_courses(self):
        """Returns all sections taught by Instructor."""
        # this method is very inefficient and doesn't actually do what the name
        # implies (collecting Sections instead of Courses); work in progress
        return Section.objects.filter(instructors=self)

    def average_rating(self):
        """Compute average rating for all this Instructor's Courses"""
        ratings = Review.objects.filter(instructor=self).aggregate(
            models.Avg('recommendability'),
            models.Avg('instructor_rating'),
            models.Avg('enjoyability'))

        recommendability = ratings.get('recommendability__avg')
        instructor_rating = ratings.get('instructor_rating__avg')
        enjoyability = ratings.get('enjoyability__avg')

        # Return None if one component is absent.
        if not recommendability or not instructor_rating or not enjoyability:
            return None

        return (recommendability + instructor_rating + enjoyability) / 3

    def average_difficulty(self):
        """Compute average difficulty for all this Instructor's Courses"""
        return Review.objects.filter(
            instructor=self).aggregate(
            models.Avg('difficulty'))['difficulty__avg']

    def average_gpa(self):
        """Compute average GPA for all this Instructor's Courses"""
        return CourseInstructorGrade.objects.filter(instructor=self).aggregate(
            models.Avg('average'))['average__avg']

    def get_courses(self):
        """Gets all Courses taught by a given Instructor"""
        # More specifically, all Courses where this Instructor has taught a Section
        # Might be good to store this data as a many-to-many field in
        # Instructor instead of computing?
        course_ids = list(
            Section.objects.filter(
                instructors=self).distinct().values_list(
                'course_id', flat=True))

        # <1000 course IDs are from super old classes...
        # should we bother keeping the data at that point?
        return Course.objects.filter(
            pk__in=course_ids).filter(
            number__gte=1000).order_by('number')


class Semester(models.Model):
    """Semester model.

    Has many Sections.
    Can belong to many Courses.
    """

    # Enumeration of possible seasons.
    SEASONS = (
        ('FALL', 'Fall'),
        ('JANUARY', 'January'),
        ('SPRING', 'Spring'),
        ('SUMMER', 'Summer'),
    )

    # Semester year. Required.
    year = models.IntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2999)])
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
    number = models.IntegerField(
        help_text="As defined in SIS/Lou's List",
        unique=True)

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
            models.Index(fields=['year', 'season']),
            models.Index(fields=['number']),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=['season', 'year'],
                name='unique semesters'
            )
        ]


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
    # Course number. Required.
    number = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99999)])

    # Subdepartment foreign key. Required.
    subdepartment = models.ForeignKey(Subdepartment, on_delete=models.CASCADE)
    # Semester that the course was most recently taught.
    semester_last_taught = models.ForeignKey(
        Semester, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.subdepartment.mnemonic} {self.number} | {self.title}"

    def code(self):
        """Returns the courses code string."""
        return f"{self.subdepartment.mnemonic} {self.number}"

    def eval_link(self):
        """Returns link to student eval page for that class"""
        link = f"https://evals.itc.virginia.edu/course-selectionguide/pages/SGMain.jsp?cmp=" \
               f"{self.subdepartment.mnemonic},{self.number}"
        return link

    def is_recent(self):
        """Returns True if course was taught in current semester."""
        return self.semester_last_taught == Semester.latest()

    def average_rating(self):
        """Compute average rating.

        Rating is defined as the average of recommendability,
        instructor rating, and enjoyability."""
        ratings = Review.objects.filter(course=self).aggregate(
            models.Avg('recommendability'),
            models.Avg('instructor_rating'),
            models.Avg('enjoyability'))

        recommendability = ratings.get('recommendability__avg')
        instructor_rating = ratings.get('instructor_rating__avg')
        enjoyability = ratings.get('enjoyability__avg')

        # Return None if one component is absent.
        if not recommendability or not instructor_rating or not enjoyability:
            return None

        return (recommendability + instructor_rating + enjoyability) / 3

    def average_difficulty(self):
        """Compute average difficulty score."""
        return Review.objects.filter(course=self).aggregate(
            models.Avg('difficulty'))['difficulty__avg']

    def review_count(self):
        """Compute total number of course reviews."""
        return self.review_set.count()

    class Meta:
        indexes = [
            models.Index(fields=['subdepartment', 'number']),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=['subdepartment', 'number'],
                name='unique course subdepartment and number'
            )
        ]


class CourseGrade(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    subdepartment = models.CharField(max_length=255)
    number = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(99999)],
        default=0)
    title = models.CharField(max_length=225, default="")
    average = models.FloatField(default=0.0)
    a_plus = models.IntegerField(default=0)
    a = models.IntegerField(default=0)
    a_minus = models.IntegerField(default=0)
    b_plus = models.IntegerField(default=0)
    b = models.IntegerField(default=0)
    b_minus = models.IntegerField(default=0)
    c_plus = models.IntegerField(default=0)
    c = models.IntegerField(default=0)
    c_minus = models.IntegerField(default=0)
    d_plus = models.IntegerField(default=0)
    d = models.IntegerField(default=0)
    d_minus = models.IntegerField(default=0)
    f = models.IntegerField(default=0)
    ot = models.IntegerField(default=0)
    drop = models.IntegerField(default=0)
    withdraw = models.IntegerField(default=0)
    total_enrolled = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.subdepartment} {self.number} {self.average}"


class CourseInstructorGrade(models.Model):
    instructor = models.ForeignKey(
        Instructor, on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=225)
    middle_name = models.CharField(max_length=225)
    last_name = models.CharField(max_length=225)
    email = models.CharField(max_length=225)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    subdepartment = models.CharField(max_length=255)
    number = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(99999)],
        default=0)
    # section_number = models.IntegerField()
    title = models.CharField(max_length=225, default="")
    average = models.FloatField(default=0.0)
    a_plus = models.IntegerField(default=0)
    a = models.IntegerField(default=0)
    a_minus = models.IntegerField(default=0)
    b_plus = models.IntegerField(default=0)
    b = models.IntegerField(default=0)
    b_minus = models.IntegerField(default=0)
    c_plus = models.IntegerField(default=0)
    c = models.IntegerField(default=0)
    c_minus = models.IntegerField(default=0)
    d_plus = models.IntegerField(default=0)
    d = models.IntegerField(default=0)
    d_minus = models.IntegerField(default=0)
    f = models.IntegerField(default=0)
    ot = models.IntegerField(default=0)
    drop = models.IntegerField(default=0)
    withdraw = models.IntegerField(default=0)
    total_enrolled = models.IntegerField(default=0)

    def __str__(self):
        return (f"{self.first_name} {self.last_name} "
                f"{self.subdepartment} {self.number} {self.average}")


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

    # Section # of units. Optional.
    units = models.CharField(max_length=10, blank=True)
    # Section section_type. Optional. e.g. 'lec' or 'lab'.
    section_type = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.course} | {self.semester} | " \
               f"{', '.join(str(i) for i in self.instructors.all())}"

    class Meta:
        indexes = [
            models.Index(fields=['semester', 'course']),
            models.Index(fields=['course']),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=['sis_section_number', 'semester'],
                name='unique sections per semesters'
            )
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
        validators=[MinValueValidator(0), MaxValueValidator(80)])
    # Review hours of reading per week. Required.
    amount_reading = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(20)])
    # Review hours of writing per week. Required.
    amount_writing = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(20)])
    # Review hours of group work per week. Required.
    amount_group = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(20)])
    # Review hours of homework per week. Required.
    amount_homework = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(20)])

    # Review created date. Required.
    created = models.DateTimeField(editable=False, default=timezone.now)
    # Review modified date. Required.
    modified = models.DateTimeField(default=timezone.now)

    # does this get used anywhere? not sure
    def average(self):
        """Average score for review."""
        return (self.instructor_rating +
                self.recommendability + self.enjoyability) / 3

    # not sure if this gets used anywhere either
    def count_votes(self):
        """Sum votes for review."""
        vote_sum = self.vote_set.aggregate(
            models.Sum('value')).get('value__sum', 0)
        if not vote_sum:
            return 0
        return vote_sum

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
    def display_reviews(course, instructor, user):
        """Prepare review list for course-instructor page."""
        reviews = Review.objects.filter(
            instructor=instructor,
            course=course,
        ).exclude(text="").annotate(
            sum_votes=models.functions.Coalesce(
                models.Sum('vote__value'),
                models.Value(0)
            ),
        )
        if user.is_authenticated:
            reviews = reviews.annotate(
                user_vote=models.functions.Coalesce(
                    models.Sum('vote__value',
                               filter=models.Q(vote__user=user)),
                    models.Value(0)
                ),
            )
        return reviews.order_by("-created")

    def __str__(self):
        return f"Review by {self.user} for {self.course} taught by {self.instructor}"

    class Meta:
        # Improve scanning of reviews by course and instructor.
        indexes = [
            models.Index(fields=['course', 'instructor']),
            models.Index(fields=['user', '-created']),
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
    value = models.IntegerField(
        validators=[MinValueValidator(-1), MaxValueValidator(1)])
    # Vote user foreign key. Required.
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Vote review foreign key. Required.
    review = models.ForeignKey(Review, on_delete=models.CASCADE)

    def __str__(self):
        return f"Vote of value {self.value} for {self.review} by {self.user}"

    class Meta:
        indexes = [
            models.Index(fields=['review']),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'review'],
                name='unique vote per user and review',
            )
        ]
