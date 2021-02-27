# pylint: disable=unused-argument
"""Django signals to implement the observer pattern"""
from typing import Union
from django.db import IntegrityError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Max
from .models import SavedCourse


@receiver(post_save, sender=SavedCourse,
          dispatch_uid='initialize_savedcourse_rank')
def initialize_savedcourse_rank(sender, instance: SavedCourse, created: bool,
                                **kwargs):
    """Initializes Savedourse.rank to a non-null integer."""
    if not created:
        return
    over: bool = False
    while not over:
        # Simplify `Union[int, None]` to `int | None` in Python 3.10
        highest_rank: Union[int, None] = SavedCourse.objects\
            .filter(user=instance.user)\
            .exclude(rank__isnull=True)\
            .aggregate(Max('rank'))['rank__max']
        instance.rank = 1 if highest_rank is None else highest_rank + 1
        try:
            instance.save()
        except IntegrityError:
            over = False
        else:
            over = True
