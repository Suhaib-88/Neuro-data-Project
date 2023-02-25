from django.urls import path
from . import views
urlpatterns = [
    path('upload-Dataset/', views.Adding_Module.as_view(),name='add-mod'),
    path('delete/<int:id>/',views.delete_data,name='delete-data'),
    path('update/<int:id>/',views.update_data,name='update-data'),
    path('import-help/',views.Import_Helper.as_view(),name='import-helper')
]

