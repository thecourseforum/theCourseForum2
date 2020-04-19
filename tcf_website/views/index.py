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
                       "img_filename": "ENG_Brian_Yu.jpg",
                       "github": "brian-yu"},
                      {"name": "Jennifer Long",
                       "role": "VP of Product Engineering",
                       "class": "2021",
                       "img_filename": "ENG_Jennifer_Long.jpg",
                       "github": "j-alicia-long"},
                      {"name": "Brad Knaysi",
                       "role": "VP of Product Engineering",
                       "class": "2020",
                       "img_filename": "ENG_Brad_Knaysi.jpg",
                       "github": "bradknaysi"},
                      {"name": "Sai Konuri",
                       "role": "VP of Infrastructure Engineering",
                       "class": "2020",
                       "img_filename": "ENG_Sai_Konuri.jpg",
                       "github": "saikonuri"},
                      {"name": "Davis DeLozier",
                       "role": "Treasurer",
                       "class": "2021",
                       "img_filename": "blank.webp",
                       "github": "dpd3mr"},
                      ]
    engineering_team = [{"name": "Brian Yu",
                         "role": "President",
                         "class": "2021",
                         "img_filename": "ENG_Brian_Yu.jpg",
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
                        {"name": "Neal Patel",
                         "role": "Developer",
                         "class": "2021",
                         "img_filename": "ENG_Neal_Patel.jpg",
                         "github": "nealpatel50"},
                        {"name": "Alex Shen",
                         "role": "Developer",
                         "class": "2023",
                         "img_filename": "ENG_Alex_Shen.jpg",
                         "github": "alex-shen1"
                         },
                        {"name": "Jack Liu",
                         "role": "Developer",
                         "class": "2023",
                         "img_filename": "ENG_Jack_Liu.jpg",
                         "github": "jackliu612"
                         },
                        {"name": "Jules Le Menestrel",
                         "role": "Developer",
                         "class": "2023",
                         "img_filename": "ENG_Jules_LeMenestrel.jpg",
                         "github": "julesfll"
                         },
                        {"name": "Jasmine Dogu",
                         "role": "Developer",
                         "class": "2022",
                         "img_filename": "ENG_Jasmine_Dogu.jpg",
                         "github": "ejd5mm"
                         },
                        {"name": "Vi Nguyen",
                         "role": "Developer",
                         "class": "2023",
                         "img_filename": "ENG_Vi_Nguyen.jpg",
                         "github": "vn6"
                         }
                        ]

    marketing_team = [{"name": "Davis DeLozier",
                       "class": "2021", "img_filename": "blank.webp"}, ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['executive_team'] = self.executive_team
        context['engineering_team'] = self.engineering_team
        context['marketing_team'] = self.marketing_team
        return context
