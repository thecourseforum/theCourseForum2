"""Views for index and about pages."""
import json
from django.template.loader import render_to_string
from django.views.generic.base import TemplateView


class IndexView(TemplateView):
    """
    Index view.

    Redirect to landing page if user not authorized.
    """
    template_name = 'landing/landing.html'

    # Load "About Team" data from json file
    def get_context_data(self, **kwargs):
        with open('tcf_website/views/team_info.json', encoding='UTF-8') as data_file:
            team_info = json.load(data_file)

        # Load FAQ data from json file, evaluating tags and filters
        rendered = render_to_string('landing/_faqs.json')
        faqs = json.loads(rendered)

        context = super().get_context_data(**kwargs)
        context['executive_team'] = team_info['executive_team']
        context['FAQs'] = faqs
        context['visited'] = self.request.session.get('visited', False)
        self.request.session['visited'] = True
        return context


class PrivacyView(TemplateView):
    """
    Privacy view.
    """
    template_name = 'about/privacy.html'


class TermsView(TemplateView):
    """
    Terms view.
    """
    template_name = 'about/terms.html'


class AboutView(TemplateView):
    """About view."""
    template_name = 'about/about.html'

    # Load data from json files
    with open('tcf_website/views/team_info.json', encoding='UTF-8') as data_file:
        team_info = json.load(data_file)

    with open('tcf_website/views/team_alums.json', encoding='UTF-8') as data_file:
        alum_info = json.load(data_file)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['executive_team'] = self.team_info['executive_team']
        context['engineering_team'] = self.team_info['engineering_team']
        context['marketing_team'] = self.team_info['marketing_team']
        context['founders'] = self.alum_info['founders']
        context['contributors'] = self.alum_info['contributors']
        return context
