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
        blog_post = json.load(data_file)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_posts'] = [self.blog_post, self.blog_post, self.blog_post]
        context['featured_posts'] = context['all_posts']
        return context

class BlogPostView(TemplateView):
    """Blog post view.
       Note: Placeholder view, may be replaced by DetailView or markdownx
    """
    template_name = 'blog/post.html'

    # Load data from json files
    with open('tcf_website/views/sample_blog_post.json') as data_file:
        blog_post = json.load(data_file)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blog_post'] = self.blog_post
        return context

def blog_posts(request):
    """Displays all blog posts."""
    posts = BlogPost.objects.all().order_by('-created_date')

    return render(request, 'blog/blog.html', {'posts': posts})

def post(request, pk):
    """Display specific blog posts"""

    post_detail = get_object_or_404(BlogPost, pk=pk)

    return render(request, 'blog/post.html', {'post_detail': post_detail})
