from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

from django.urls import re_path
from django.views.static import serve
from django.conf import settings

def empty_response(request):
    return HttpResponse('')


urlpatterns = [
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
    
    path('admin/', admin.site.urls),
    path('', empty_response),
    path('incomes/', include('incomes.urls')),
]


