from django.urls import path
from . import views

urlpatterns = [
    # Income URLs
    path('', views.IncomeListView.as_view(), name='income-list'),
    path('income/<int:pk>/', views.IncomeDetailView.as_view(), name='income-detail'),
    path('income/add/', views.IncomeCreateView.as_view(), name='income-create'),
    path('income/<int:pk>/edit/', views.IncomeUpdateView.as_view(), name='income-update'),
    path('income/<int:pk>/delete/', views.IncomeDeleteView.as_view(), name='income-delete'),

    # Category URLs
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('categories/add/', views.CategoryCreateView.as_view(), name='category-create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category-update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category-delete'),

    # UserProfile URLs
    path('profile/', views.UserProfileDetailView.as_view(), name='userprofile-detail'),
    path('profile/edit/', views.UserProfileUpdateView.as_view(), name='userprofile-update'),

    # Auth URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('logged_out/', views.CustomLogoutView.as_view(), name='logged_out'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

]
