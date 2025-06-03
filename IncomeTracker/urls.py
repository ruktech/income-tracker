from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.urls import re_path
from django.views.static import serve
from django.conf import settings

def main_page(request):
    return render(request, 'main.html')

urlpatterns = [
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
    path('admin/', admin.site.urls),
    path('', main_page, name='main'),
    path('incomes/', include('incomes.urls')),
]