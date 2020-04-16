# pylint: disable=missing-class-docstring, wildcard-import

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

    def average_rating_for_course(self, course):
        """Compute average of instructor and recommend scores."""
        ratings = Review.objects.filter(
            course=course, instructor=self).aggregate(
                models.Avg('recommendability'),
                models.Avg('instructor_rating'))

        recommendability = ratings.get('recommendability__avg')
        instructor_rating = ratings.get('instructor_rating__avg')

        # Return None if one component is absent.
        if not recommendability or not instructor_rating:
            return None

        return (recommendability + instructor_rating) / 2

    def average_difficulty_for_course(self, course):
        """Compute average difficulty score."""
        return Review.objects.filter(
            course=course, instructor=self).aggregate(
                models.Avg('difficulty'))['difficulty__avg']

    def average_hours_for_course(self, course):
        """Compute average hrs/wk."""
        return Review.objects.filter(
            course=course, instructor=self).aggregate(
                models.Avg('hours_per_week'))['hours_per_week__avg']


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
        return f"{self.subdepartment.mnemonic} {self.number} {self.title}"

    def code(self):
        """Returns the courses code string."""
        return f"{self.subdepartment.mnemonic} {self.number}"

    def is_recent(self):
        """Returns True if course was taught in current semester."""
        return self.semester_last_taught == Semester.latest()

    def average_rating(self):
        """Compute average rating."""
        return Review.objects.filter(course=self).aggregate(
            models.Avg('recommendability'))['recommendability__avg']

    def average_difficulty(self):
        """Compute average difficulty score."""
        return Review.objects.filter(course=self).aggregate(
            models.Avg('difficulty'))['difficulty__avg']

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
        return f"{self.course} {self.semester} {', '.join(str(i) for i in self.instructors.all())}"

    class Meta:
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
    # Review hours per week. Required.
    hours_per_week = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(168)])
    # Review created date. Required.
    created = models.DateTimeField(editable=False, default=timezone.now)
    # Review modified date. Required.
    modified = models.DateTimeField(default=timezone.now)

    # After data migration, add the following in order to automatically
    # save created and modified dates.

    # def save(self, *args, **kwargs):
    #     ''' On save, update timestamps '''
    #     if not self.id:
    #         self.created = timezone.now()
    #     self.modified = timezone.now()
    #     return super(Review, self).save(*args, **kwargs)

    def average(self):
        """Average score for review."""
        return (self.instructor_rating + self.recommendability) / 2

    def __str__(self):
        return f"Review by {self.user} for {self.course} taught by {self.instructor}"

    class Meta:
        # Improve scanning of reviews by course and instructor.
        indexes = [
            models.Index(fields=['course', 'instructor']),
            models.Index(fields=['user', ]),
        ]

        # Some of the tCF 1.0 data did not honor this constraint.
        # Should we add it and remove duplicates from old data?

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
