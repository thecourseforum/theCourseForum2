from datetime import timezone

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

class School(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)

class Department(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)

    school = models.ForeignKey(School, on_delete=models.CASCADE)

# e.g. CREO in French department or ENCW in English
class Subdepartment(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    mnemonic = models.CharField(max_length=255)

    department = models.ForeignKey(Department, on_delete=models.CASCADE)

class User(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    computing_id = models.CharField(max_length=10, unique=True, blank=True)

    class Meta:
        abstract = True

class Student(User):
    confirmed = models.BooleanField(default=False)
    graduation_year = models.IntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2999)],
        blank=True)

class Instructor(User):
    website = models.URLField(blank=True)
    departments = models.ManyToManyField(Department)

class Semester(models.Model):

    SEASONS = (
        ('FALL', 'Fall'),
        ('WINTER', 'Winter'),
        ('SPRING', 'Spring'),
        ('SUMMER', 'Summer'),
    )

    year = models.IntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2999)])
    season = models.CharField(max_length=6, choices=SEASONS)

    number = models.IntegerField(help_text="As defined in SIS/Lou's List")

class Course(models.Model):
    title = models.CharField(max_length=255)
    topic = models.TextField(blank=True)
    description = models.TextField(blank=True)
    number = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99999)])
    
    units = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)])

    subdepartment = models.ForeignKey(Subdepartment, on_delete=models.CASCADE)
    semester_last_taught = models.ForeignKey(Semester, on_delete=models.CASCADE)

class Section(models.Model):
    sis_section_number = models.IntegerField(unique=True)
    instructors = models.ManyToManyField(Instructor)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

class Review(models.Model):
    text = models.TextField()
    author = models.ForeignKey(Student, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    RATINGS = (
        (1, 1.0),
        (2, 2.0),
        (3, 3.0),
        (4, 4.0),
        (5, 5.0),
    )
    professor_rating = models.FloatField(choices=RATINGS)
    difficulty = models.FloatField(choices=RATINGS)
    recommendability = models.FloatField(choices=RATINGS)
    hours_per_week = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(168)])
    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(Review, self).save(*args, **kwargs)

class Vote(models.Model):
    value = models.IntegerField(
        validators=[MinValueValidator(-1), MaxValueValidator(1)])
    voter = models.ForeignKey(Student, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE)