# frontend/views.py
from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import HttpResponseNotFound

class FrontendAppView(TemplateView):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except:
            return HttpResponseNotFound("index.html not found. Did you run `npm run build`?")


