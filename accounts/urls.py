from django.urls import path
from . import views
from dataIngestion.views import projects_view
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.Login,name='login-page'),
    path('register/', views.Register,name='register-page'),
    path('home/', views.Home,name='home'),
    path('home/<int:userID>',projects_view.as_view(), name='projects'),
    path('accounts/logout/',views.Logout,name='logout-page'),
    path('accounts/changePassword/', views.change_password, name='change_password'),
]