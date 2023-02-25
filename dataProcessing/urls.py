from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('Overview/<str:id>/', views.Project.as_view(),name='project'),
    path("setTarget/<str:id>/", views.Set_Target.as_view() ,name="target"),
    path('export-help/',views.export_helper,name='export-helper'),
    path('export-File/',views.export_data,name='export'),
    path('export-resources/',views.export_resources,name='export-resource'),
    path('Generate-Reports/',views.generate_project_Reports,name='project-reports'),
    path('Actions-History/',views.project_action_history,name='action-history'),
    path('Custom-Script/',views.Custom_script, name='custom-operation'),
    path('help/',views.get_help,name='helper'),

]