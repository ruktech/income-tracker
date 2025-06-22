from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import include, path


def main_page(request: HttpRequest) -> HttpResponse:
    return render(request, "main.html")


urlpatterns = [
    # re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
    path("admin/", admin.site.urls),
    path("", main_page, name="main"),
    path("incomes/", include("incomes.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
