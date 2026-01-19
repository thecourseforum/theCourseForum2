"""Views for site-wide Q&A Forum."""

import json

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import TrigramSimilarity
from django.core.exceptions import PermissionDenied
from django.db.models import Count, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..models import Course, Semester, Subdepartment
from ..models.models import (
    ForumCategory,
    ForumPost,
    ForumPostVote,
    ForumResponse,
    ForumResponseVote,
)


class ForumPostForm(forms.ModelForm):
    """Form for creating/editing forum posts."""

    course_search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Search for a course (e.g., CS 2100)...",
                "autocomplete": "off",
            }
        ),
    )

    class Meta:
        model = ForumPost
        fields = ["title", "content", "course", "category"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter post title..."}
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Describe your question or topic...",
                    "rows": 5,
                }
            ),
            "course": forms.HiddenInput(),
            "category": forms.Select(attrs={"class": "form-control"}),
        }


class ForumResponseForm(forms.ModelForm):
    """Form for creating/editing forum responses."""

    class Meta:
        model = ForumResponse
        fields = ["content", "semester", "parent"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "form-control reply-textarea",
                    "placeholder": "Write a response...",
                    "rows": 3,
                }
            ),
            "semester": forms.Select(attrs={"class": "form-control"}),
            "parent": forms.HiddenInput(),
        }


def forum_dashboard(request):
    """Main forum dashboard view."""
    # Get filter parameters
    search_query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "")
    course_filter = request.GET.get("course", "")
    page_number = request.GET.get("page", 1)
    selected_post_id = request.GET.get("post", None)

    # Build posts query
    posts = ForumPost.objects.filter(is_hidden=False).select_related(
        "user", "course", "course__subdepartment", "category"
    )

    # Apply filters
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) | Q(content__icontains=search_query)
        )

    if category_slug:
        posts = posts.filter(category__slug=category_slug)

    if course_filter:
        posts = posts.filter(course_id=course_filter)

    # Annotate with vote and reply counts
    posts = posts.annotate(
        vote_count=Coalesce(Sum("forumpostvote__value"), Value(0)),
        reply_count=Count("forumresponse", filter=Q(forumresponse__is_hidden=False)),
    )

    # Add user vote if authenticated
    if request.user.is_authenticated:
        posts = posts.annotate(
            user_vote=Coalesce(
                Sum("forumpostvote__value", filter=Q(forumpostvote__user=request.user)),
                Value(0),
            )
        )

    # Order posts
    posts = posts.order_by("-is_pinned", "-created")

    # Get categories for filter dropdown
    categories = ForumCategory.objects.all()

    # Get selected post details
    selected_post = None
    responses = []

    if selected_post_id:
        try:
            selected_post = posts.get(id=selected_post_id)
            responses = get_post_responses(selected_post, request.user)
        except ForumPost.DoesNotExist:
            pass
    elif posts.exists():
        # Default to first post
        selected_post = posts.first()
        if selected_post:
            responses = get_post_responses(selected_post, request.user)

    # Get semesters for response form
    semesters = Semester.objects.order_by("-number")[:20]

    context = {
        "posts": posts,
        "categories": categories,
        "selected_post": selected_post,
        "responses": responses,
        "semesters": semesters,
        "search_query": search_query,
        "selected_category": category_slug,
        "selected_course": course_filter,
    }

    return render(request, "forum/forum_dashboard.html", context)


def get_post_responses(post, user):
    """Get responses for a post with nested replies."""
    # Get top-level responses (no parent)
    responses = (
        ForumResponse.objects.filter(post=post, parent__isnull=True, is_hidden=False)
        .select_related("user", "semester")
        .annotate(vote_count=Coalesce(Sum("forumresponsevote__value"), Value(0)))
    )

    if user and user.is_authenticated:
        responses = responses.annotate(
            user_vote=Coalesce(
                Sum("forumresponsevote__value", filter=Q(forumresponsevote__user=user)),
                Value(0),
            )
        )

    # Build nested structure
    result = []
    for response in responses:
        response.nested_replies = response.get_nested_replies(user)
        result.append(response)

    return result


def forum_post_detail(request, post_id):
    """API endpoint to get post details."""
    post = get_object_or_404(ForumPost, id=post_id, is_hidden=False)

    # Get vote info
    vote_count = post.vote_score()
    user_vote = 0

    if request.user.is_authenticated:
        user_vote_obj = ForumPostVote.objects.filter(
            user=request.user, post=post
        ).first()
        if user_vote_obj:
            user_vote = user_vote_obj.value

    # Get responses
    responses = get_post_responses(post, request.user)

    # Get semesters for response form
    semesters = Semester.objects.order_by("-number")[:20]

    context = {
        "post": post,
        "responses": responses,
        "vote_count": vote_count,
        "user_vote": user_vote,
        "semesters": semesters,
    }

    return render(request, "forum/_post_detail.html", context)


@login_required
def create_post(request):
    """Create a new forum post."""
    if request.method == "POST":
        form = ForumPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "post_id": post.id,
                        "message": "Post created successfully!",
                    }
                )

            messages.success(request, "Post created successfully!")
            return redirect("forum_dashboard")
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "errors": form.errors}, status=400
                )

            messages.error(request, "Please correct the errors below.")

    # GET request - show form
    categories = ForumCategory.objects.all()
    return render(request, "forum/_new_post_form.html", {"categories": categories})


@login_required
@require_POST
def edit_post(request, post_id):
    """Edit an existing forum post."""
    post = get_object_or_404(ForumPost, id=post_id)

    if post.user != request.user:
        raise PermissionDenied("You can only edit your own posts.")

    form = ForumPostForm(request.POST, instance=post)
    if form.is_valid():
        form.save()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {"success": True, "message": "Post updated successfully!"}
            )

        messages.success(request, "Post updated successfully!")
        return redirect("forum_dashboard")

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    return redirect("forum_dashboard")


@login_required
@require_POST
def delete_post(request, post_id):
    """Delete a forum post."""
    post = get_object_or_404(ForumPost, id=post_id)

    if post.user != request.user:
        raise PermissionDenied("You can only delete your own posts.")

    post.is_hidden = True
    post.save()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": True, "message": "Post deleted successfully!"})

    messages.success(request, "Post deleted successfully!")
    return redirect("forum_dashboard")


@login_required
@require_POST
def vote_post(request, post_id):
    """Vote on a forum post."""
    post = get_object_or_404(ForumPost, id=post_id)

    try:
        data = json.loads(request.body)
        vote_type = data.get("vote_type")
    except json.JSONDecodeError:
        vote_type = request.POST.get("vote_type")

    if vote_type == "up":
        post.upvote(request.user)
    elif vote_type == "down":
        post.downvote(request.user)
    else:
        return JsonResponse(
            {"success": False, "error": "Invalid vote type"}, status=400
        )

    # Get updated vote count and user's current vote
    new_vote_count = post.vote_score()
    user_vote_obj = ForumPostVote.objects.filter(user=request.user, post=post).first()
    user_vote = user_vote_obj.value if user_vote_obj else 0

    return JsonResponse(
        {"success": True, "vote_count": new_vote_count, "user_vote": user_vote}
    )


@login_required
def create_response(request, post_id):
    """Create a response to a forum post."""
    post = get_object_or_404(ForumPost, id=post_id)

    if post.is_locked:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": False,
                    "error": "This post is locked and cannot receive new responses.",
                },
                status=403,
            )
        messages.error(request, "This post is locked.")
        return redirect("forum_dashboard")

    if request.method == "POST":
        form = ForumResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.post = post
            response.user = request.user
            response.save()

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "response_id": response.id,
                        "message": "Response posted successfully!",
                    }
                )

            messages.success(request, "Response posted successfully!")
            return redirect(f"/forum/?post={post_id}")
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "errors": form.errors}, status=400
                )

    return redirect(f"/forum/?post={post_id}")


@login_required
@require_POST
def edit_response(request, response_id):
    """Edit a forum response."""
    response = get_object_or_404(ForumResponse, id=response_id)

    if response.user != request.user:
        raise PermissionDenied("You can only edit your own responses.")

    content = request.POST.get("content", "").strip()
    if not content:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {"success": False, "error": "Response content cannot be empty."},
                status=400,
            )
        return redirect("forum_dashboard")

    response.content = content
    response.save()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {"success": True, "message": "Response updated successfully!"}
        )

    messages.success(request, "Response updated successfully!")
    return redirect(f"/forum/?post={response.post_id}")


@login_required
@require_POST
def delete_response(request, response_id):
    """Delete a forum response."""
    response = get_object_or_404(ForumResponse, id=response_id)

    if response.user != request.user:
        raise PermissionDenied("You can only delete your own responses.")

    post_id = response.post_id
    response.is_hidden = True
    response.save()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {"success": True, "message": "Response deleted successfully!"}
        )

    messages.success(request, "Response deleted successfully!")
    return redirect(f"/forum/?post={post_id}")


@login_required
@require_POST
def vote_response(request, response_id):
    """Vote on a forum response."""
    response = get_object_or_404(ForumResponse, id=response_id)

    try:
        data = json.loads(request.body)
        vote_type = data.get("vote_type")
    except json.JSONDecodeError:
        vote_type = request.POST.get("vote_type")

    if vote_type == "up":
        response.upvote(request.user)
    elif vote_type == "down":
        response.downvote(request.user)
    else:
        return JsonResponse(
            {"success": False, "error": "Invalid vote type"}, status=400
        )

    # Get updated vote count
    new_vote_count = response.vote_score()
    user_vote_obj = ForumResponseVote.objects.filter(
        user=request.user, response=response
    ).first()
    user_vote = user_vote_obj.value if user_vote_obj else 0

    return JsonResponse(
        {"success": True, "vote_count": new_vote_count, "user_vote": user_vote}
    )


def search_courses(request):
    """API endpoint to search courses for the post form."""
    query = request.GET.get("q", "").strip()

    if len(query) < 2:
        return JsonResponse({"results": []})

    # Use trigram similarity for fuzzy matching
    courses = (
        Course.objects.annotate(
            similarity=TrigramSimilarity("combined_mnemonic_number", query)
        )
        .filter(similarity__gte=0.1)
        .select_related("subdepartment")
        .order_by("-similarity")[:10]
    )

    results = [
        {
            "id": course.id,
            "code": f"{course.subdepartment.mnemonic} {course.number}",
            "title": course.title,
        }
        for course in courses
    ]

    return JsonResponse({"results": results})


def get_categories(request):
    """API endpoint to get all categories."""
    categories = ForumCategory.objects.all()
    return JsonResponse(
        {
            "categories": [
                {"id": cat.id, "name": cat.name, "slug": cat.slug, "color": cat.color}
                for cat in categories
            ]
        }
    )
