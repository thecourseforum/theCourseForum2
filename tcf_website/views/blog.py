"""Views for blog pages."""
import json
from django.template.loader import render_to_string
from django.views.generic.base import TemplateView
from ..models import BlogPost
from django.shortcuts import render,get_object_or_404


class BlogView(TemplateView):
    """Blog view."""
    template_name = 'blog/blog.html'

    # Load data from json files
    with open('tcf_website/views/sample_blog_post.json') as data_file:
        sample_post = json.load(data_file)

    posts = BlogPost.objects.all().order_by('-created_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_posts'] = [self.sample_post, self.sample_post, self.sample_post]
        context['all_posts'] = context['featured_posts'] # Placeholder posts
        context['posts'] = self.posts
        return context

def post(request, pk):
    """Display specific blog posts"""
    # TODO: Replace with DetailView

    post_detail = get_object_or_404(BlogPost, pk=pk)

    return render(request, 'blog/post.html', {'post_detail': post_detail})
