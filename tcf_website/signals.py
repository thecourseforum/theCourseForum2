from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SavedCourse


@receiver(post_save, sender=SavedCourse, dispatch_uid='initialize_savedcourse_rank')
def initialize_savedcourse_rank(sender, instance: SavedCourse, created: bool,
                                **kwargs):
    if not created:
        return
    over: bool = False
    while not over:
        try:
            saved_course_with_last_rank: SavedCourse = SavedCourse.objects\
                .filter(user=instance.user)\
                .exclude(rank__isnull=True)\
                .latest('rank')
        except SavedCourse.DoesNotExist:
            instance.rank = 'A'
        else:
            instance.rank = SavedCourse.get_next_rank(
                saved_course_with_last_rank.rank)
        try:
            instance.save()
        except:
            over = False
        else:
            over = True
