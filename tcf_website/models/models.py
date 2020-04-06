from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class School(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return self.name

class Department(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)

    school = models.ForeignKey(School, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'school'],
                name='unique departments per school'
            )
        ]

# e.g. CREO in French department or ENCW in English
class Subdepartment(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    mnemonic = models.CharField(max_length=255, unique=True)

    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.mnemonic} - {self.name}"

    # courses within the last 5 years.
    def recent_courses(self):
        latest_semester = Semester.latest()
        return self.course_set.filter(semester_last_taught__year__gte=latest_semester.year-5).order_by("number")
    
    def has_current_course(self):
        return self.course_set.filter(section__semester=Semester.latest()).exists()
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['mnemonic', 'department'],
                name='unique subdepartment mnemonics per department'
            )
        ]

class User(AbstractUser):
    computing_id = models.CharField(max_length=20, unique=True, blank=True)
    graduation_year = models.IntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2999)],
        blank=True, null=True
    )
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Instructor(models.Model):
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    departments = models.ManyToManyField(Department)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Semester(models.Model):

    SEASONS = (
        ('FALL', 'Fall'),
        ('JANUARY', 'January'),
        ('SPRING', 'Spring'),
        ('SUMMER', 'Summer'),
    )

    year = models.IntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2999)])
    season = models.CharField(max_length=7, choices=SEASONS)

    number = models.IntegerField(help_text="As defined in SIS/Lou's List", unique=True)

    def __repr__(self):
        return f"{self.year} {self.season.title()} ({self.number})"
    
    def __str__(self):
        return f"{self.season.title()} {self.year}"
    
    def is_after(self, other_sem):
        return self.number > other_sem.number
    
    def latest():
        return Semester.objects.order_by("-number").first()
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['season', 'year'],
                name='unique semesters'
            )
        ]

class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    number = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99999)])

    subdepartment = models.ForeignKey(Subdepartment, on_delete=models.CASCADE)
    semester_last_taught = models.ForeignKey(Semester, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.subdepartment.mnemonic} {self.number} {self.title}"
    
    def code(self):
        return f"{self.subdepartment.mnemonic} {self.number}"
    
    def is_recent(self):
        return self.semester_last_taught == Semester.latest()
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subdepartment', 'number'],
                name='unique course subdepartment and number'
            )
        ]

class Section(models.Model):
    sis_section_number = models.IntegerField() # NOTE: not unique!
    instructors = models.ManyToManyField(Instructor)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    topic = models.TextField(blank=True)

    units = models.CharField(max_length=10, blank=True)
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
    text = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    RATINGS = (
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 5),
    )
    instructor_rating = models.PositiveSmallIntegerField(choices=RATINGS)
    difficulty = models.PositiveSmallIntegerField(choices=RATINGS)
    recommendability = models.PositiveSmallIntegerField(choices=RATINGS)
    hours_per_week = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(168)])
    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField()

    # def save(self, *args, **kwargs):
    #     ''' On save, update timestamps '''
    #     if not self.id:
    #         self.created = timezone.now()
    #     self.modified = timezone.now()
    #     return super(Review, self).save(*args, **kwargs)
    
    def __str__(self):
        return f"Review by {self.user} for {self.course} taught by {self.instructor}"
    
    # class Meta:
    #     constraints = [
    #         models.UniqueConstraint(
    #             fields=['user', 'course', 'instructor'],
    #             name='unique review per user, course, and instructor',
    #         )
    #     ]

class Vote(models.Model):
    value = models.IntegerField(
        validators=[MinValueValidator(-1), MaxValueValidator(1)])
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE)

    def __str__(self):
        return f"Vote of value {self.value} for {self.review} by {self.user}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'review'],
                name='unique vote per user and review',
            )
        ]