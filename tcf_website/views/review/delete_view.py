"""Review deletion (class-based)."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.views import generic

from ...models import Review
from ...utils import safe_next_url


class DeleteReview(LoginRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    """Review deletion view."""

    model = Review
    success_url = reverse_lazy("reviews")

    def get_success_url(self):
        """Use caller-provided next URL when safe, otherwise default."""
        return safe_next_url(self.request, str(self.success_url))

    def get_object(self):  # pylint: disable=arguments-differ
        """Override DeleteView's function to validate review belonging to user."""
        obj = super().get_object()
        if obj.user != self.request.user:
            raise PermissionDenied("You are not allowed to delete this review!")
        return obj

    def get_success_message(self, cleaned_data) -> str:
        """Overrides SuccessMessageMixin's get_success_message method."""
        if self.object.club:
            return f"Successfully deleted your review for {self.object.club}!"
        return f"Successfully deleted your review for {self.object.course}!"
