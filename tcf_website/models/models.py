from datetime import timezone

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import AbstractUser

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

# e.g. CREO in French department or ENCW in English
class Subdepartment(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    mnemonic = models.CharField(max_length=255)

    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class User(AbstractUser):
    computing_id = models.CharField(max_length=10, unique=True, blank=True)
    graduation_year = models.IntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2999)],
        blank=True, null=True
    )
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class Instructor(models.Model):
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    departments = models.ManyToManyField(Department)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

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

    number = models.IntegerField(help_text="As defined in SIS/Lou's List")

    def __str__(self):
        return f"{self.year} {self.season.title()}"

class Course(models.Model):
    title = models.CharField(max_length=255)
    topic = models.TextField(blank=True)
    description = models.TextField(blank=True)
    number = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99999)])
    
    units = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        blank=True, null=True)

    subdepartment = models.ForeignKey(Subdepartment, on_delete=models.CASCADE)
    semester_last_taught = models.ForeignKey(Semester, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.subdepartment.mnemonic} {self.number}"

class Section(models.Model):
    sis_section_number = models.IntegerField() # NOTE: not unique!
    instructors = models.ManyToManyField(Instructor)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.course} {self.semester} {', '.join(self.instructors.all())}"

class Review(models.Model):
    text = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
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
    
    def __str__(self):
        return f"Review by {self.author} for {self.section}"

class Vote(models.Model):
    value = models.IntegerField(
        validators=[MinValueValidator(-1), MaxValueValidator(1)])
    voter = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE)

    def __str__(self):
        return f"Vote of value {self.value} for {self.eview} by {self.voter}"