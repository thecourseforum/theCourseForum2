class CourseEnrollment(models.Model):
    course = models.OneToOneField('Course', on_delete=models.CASCADE, related_name='enrollment_tracking')
    last_update = models.DateTimeField(auto_now=True)
    update_count = models.IntegerField(default=0)  # Optional: track number of updates
    
    def __str__(self):
        return f"Enrollment tracking for {self.course.code()}" 