"""Views for index and about pages."""
from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView


def index(request):
    """
    Index view.

    Redirect to landing page if user not authorized, otherwise show
    browse page.
    """
    if request.user.is_authenticated:
        return redirect('browse')
    return render(request, 'landing/landing.html')


def privacy(request):
    """Privacy view."""
    return render(request, 'about/privacy.html')


def terms(request):
    """Terms view."""
    return render(request, 'about/terms.html')


class AboutView(TemplateView):
    """About view."""
    template_name = 'about/about.html'
    executive_team = [{"name": "Brian Yu",
                       "role": "President",
                       "class": "2021",
                       "img_filename": "ENG_Brian_Yu.jpeg",
                       "github": "brian-yu"},
                      {"name": "Sai Konuri",
                       "role": "VP of Infrastructure Engineering",
                       "class": "2020",
                       "img_filename": "ENG_Sai_Konuri.jpg",
                       "github": "saikonuri"},
                      {"name": "Brad Knaysi",
                       "role": "VP of Product Engineering",
                       "class": "2020",
                       "img_filename": "ENG_Brad_Knaysi.jpg",
                       "github": "bradknaysi"},
                      {"name": "Jennifer Long",
                       "role": "VP of Product Engineering",
                       "class": "2021",
                       "img_filename": "ENG_Jennifer_Long.jpg",
                       "github": "j-alicia-long"},
                      {"name": "Davis DeLozier",
                       "role": "Treasurer",
                       "class": "2021",
                       "img_filename": "ENG_Brian_Yu.jpeg",
                       "github": "dpd3mr"},
                      ]
    engineering_team = [{"name": "Brian Yu",
                         "role": "President",
                         "class": "2021",
                         "img_filename": "ENG_Brian_Yu.jpeg",
                         "github": "brian-yu"},
                        {"name": "Sai Konuri",
                         "role": "VP of Infrastructure Engineering",
                         "class": "2020",
                         "img_filename": "ENG_Sai_Konuri.jpg",
                         "github": "saikonuri"},
                        {"name": "Brad Knaysi",
                         "role": "VP of Product Engineering",
                         "class": "2020",
                         "img_filename": "ENG_Brad_Knaysi.jpg",
                         "github": "bradknaysi"},
                        {"name": "Jennifer Long",
                         "role": "VP of Product Engineering",
                         "class": "2021",
                         "img_filename": "ENG_Jennifer_Long.jpg",
                         "github": "j-alicia-long"},
                        {"name": "Nikash Sethi",
                         "role": "Developer",
                         "class": "2021",
                         "img_filename": "ENG_Nikash_Sethi.jpg",
                         "github": "nikashs"},
                        {"name": "Alex Shen",
                         "role": "Developer",
                         "class": "2023",
                         "img_filename": "ENG_Alex_Shen.jpg",
                         "github": "alex-shen1"
                         }
                        ]

    marketing_team = [
        {"name": "Brian Yu", "class": "2021", "img_filename": "ENG_Brian_Yu.jpeg"},
        {"name": "Sai Konuri", "class": "2020",
            "img_filename": "ENG_Sai_Konuri.jpg"},
        {"name": "Brad Knaysi", "class": "2020",
            "img_filename": "ENG_Brad_Knaysi.jpg"},
        {"name": "Jennifer Long", "class": "2021",
            "img_filename": "ENG_Jennifer_Long.jpg"},
        {"name": "Davis DeLozier", "class": "2021",
            "img_filename": "ENG_Brian_Yu.jpeg"},
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['executive_team'] = self.executive_team
        context['engineering_team'] = self.engineering_team
        context['marketing_team'] = self.marketing_team
        return context
