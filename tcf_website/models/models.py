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
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['mnemonic', 'department'],
                name='unique subdepartment mnemonics per department'
            )
        ]

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

    number = models.IntegerField(help_text="As defined in SIS/Lou's List", unique=True)

    def __str__(self):
        return f"{self.year} {self.season.title()} ({self.number})"
    
    def is_after(self, other_sem):
        season_val = {
            'JANUARY': 1,
            'SPRING': 2,
            'SUMMER': 3,
            'FALL': 4,
        }
        return self.year > other_sem.year and season_val[self.season] > season_val[other_sem.season]
    
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
        return f"{self.subdepartment.mnemonic} {self.number}"
    
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
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'course', 'instructor'],
                name='unique review per author, course, and instructor',
            )
        ]

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